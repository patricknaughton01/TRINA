import klampt
from klampt.plan import cspace,robotplanning
from klampt.io import resource
from klampt.model import trajectory
import time

world = klampt.WorldModel()
world.readFile("Klampt-examples/data/tx90cuptable.xml")
robot = world.robot(0)

#this is the CSpace that will be used.  Standard collision and joint limit constraints
#will be checked
space = robotplanning.makeSpace(world,robot,edgeCheckResolution=0.05)

#fire up a visual editor to get some start and goal configurations
qstart = robot.getConfig()
qgoal = robot.getConfig()
save,qstart = resource.edit("Start config",qstart,"Config",world=world)
#it's worthwile to make sure that it's feasible
while save and not space.feasible(qstart): #if save is true (user press OK) and starting point is feasible
    print "Start configuration isn't feasible, please pick one that is collision-free"
    save,qstart = resource.edit("Start config",qstart,"Config",world=world)

save,qgoal = resource.edit("Goal config",qgoal,"Config",world=world)
while save and not space.feasible(qgoal):#if save is true (user press OK) and goal point is feasible
    print "Goal configuration isn't feasible, please pick one that is collision-free"
    save,qgoal = resource.edit("Goal config",qgoal,"Config",world=world)

settings = {'type':'rrt',
    'perturbationRadius':0.25, #maximum expansion radius for RRT and SBL.
    'bidirectional':True, #1 if bidirectional planning should be used. Valid for RRT, SBL, RRT*.
    'shortcut':True, #1 if post-processing smoothing should be used. Turns a planner into an optimizing planner.
    'restart':True,#1 if random-restarts should be used, turns a planner into an optimizing planner. If activated, restartTermCond must be present as well
    'restartTermCond':"{foundSolution:1,maxIters:1000}" # a string that can be converted into a JSON object describing the termination condition. 
    #For example, "{foundSolution:1,maxIters:1000}" restarts the underlying planner if it found a solution and spent 1000 iterations of planning.
}
t0 = time.time()
print "Creating planner..."
#Manual construction of planner
planner = cspace.MotionPlan(space, **settings)
planner.setEndpoints(qstart,qgoal)
print "qstart:", qstart
print "qgoal", qgoal
print "Planner creation time",time.time()-t0
t0 = time.time()
print "Planning..."
numIters = 0
for round in range(10):
    planner.planMore(500)
    numIters += 1
    if planner.getPath() is not None:
      break
print "Planning time,",numIters,"iterations",time.time()-t0

path = planner.getPath()
if path is not None:
    print "Got a path with",len(path),"milestones"
else:
    print "No feasible path was found"




#provide some debugging information
V,E = planner.getRoadmap()#list of configurations (vertices) and edges
print len(V),"feasible milestones sampled,",len(E),"edges connected"

print "CSpace stats:"
spacestats = space.getStats()
for k in sorted(spacestats.keys()):
    print " ",k,":",spacestats[k]

print "Planner stats:"
planstats = planner.getStats()
for k in sorted(planstats.keys()):
    print " ",k,":",planstats[k]

if path:
    #save planned milestone path to disk
    print "Saving to my_plan.configs"
    resource.set("my_plan.configs",path,"Configs")

    #visualize path as a Trajectory resource
    traj = trajectory.RobotTrajectory(robot,range(len(path)),path)
    resource.edit("Planned trajectory",traj,world=world)

    #Here's another way to do it: visualize path in the vis module
    from klampt import vis
    vis.add("world",world)
    vis.animate(("world",robot.getName()),path)
    vis.add("trajectory",traj)   #this draws the end effector trajectory
    vis.spin(float('inf'))

#play nice with garbage collection
planner.space.close()
planner.close()