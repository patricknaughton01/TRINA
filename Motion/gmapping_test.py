import klampt
import time
import math
from klampt import vis, Geometry3D
from klampt.io import ros
from klampt.math import so2

from motion import *

import rospy
import tf
import sensor_msgs

from multiprocessing import Process, Pipe

def add_terrain(world, path, T, name):
    geom = Geometry3D()
    geom.loadFile(path)
    geom.transform(T[0], T[1])
    item = world.makeTerrain(name)
    item.geometry().set(geom)
    return item

def publish_tf(curr_pose):
    x, y, theta = curr_pose
    theta = theta % (math.pi*2)
    br = tf.TransformBroadcaster()
    br.sendTransform([x, y, 0], tf.transformations.quaternion_from_euler(0, 0, theta), rospy.Time.now(), "base_link", "odom")
    br.sendTransform([0.2, 0, 0.2], tf.transformations.quaternion_from_euler(0, 0, 0), rospy.Time.now(), "base_scan", "base_link")

def interpolate(a, b, u):
    return (b-a)*u + a

def lidar_to_pc(robot, sensor, scan):
    x, y, theta = robot.base_state.measuredPos

    angle_range = float(sensor.getSetting("xSweepMagnitude"))
    rv = klampt.PointCloud()

    for i in range(len(scan)):
        u = float(i)/float(len(scan))
        # If period = 0, measurement sweeps over range of [-magnitude,magnitude]
        angle = interpolate(-angle_range, angle_range, u)
        pt = [math.cos(angle), math.sin(angle)]
        pt[0] *= scan[i]
        pt[1] *= scan[i]
        pt[0] += 0.2    # lidar is 0.2 offset (in x direction) from robot
        pt = so2.apply(theta, pt)
        pt[0] += x
        pt[1] += y
        pt.append(0.2)  # height is 0.2

        rv.addPoint(pt)

    return rv

robot = Motion(mode = "Kinematic", codename="anthrax")

leftTuckedConfig = [0.7934980392456055, -2.541288038293356, -2.7833543555, 4.664876623744629, -0.049166981373, 0.09736919403076172]
leftUntuckedConfig = [-0.2028,-2.1063,-1.610,3.7165,-0.9622,0.0974]
rightTuckedConfig = robot.mirror_arm_config(leftTuckedConfig)
rightUntuckedConfig = robot.mirror_arm_config(leftUntuckedConfig)

robot.startup()

# reset arms
robot.setLeftLimbPositionLinear(leftTuckedConfig,5)
robot.setRightLimbPositionLinear(rightTuckedConfig,5)

world = robot.getWorld()
add_terrain(world, "./data/cube.off", ([1, 0, 0, 0, 1, 0, 0, 0, 1], [2, 2, 0]), "test")
add_terrain(world, "./data/cube.off", ([1, 0, 0, 0, 1, 0, 0, 0, 1], [-2, 2, 0]), "test1")
add_terrain(world, "./data/cube.off", ([1, 0, 0, 0, 1, 0, 0, 0, 1], [2, -2, 0]), "test2")
add_terrain(world, "./data/cube.off", ([1, 0, 0, 0, 1, 0, 0, 0, 1], [-2, -2, 0]), "test3")

add_terrain(world, "./data/cube.off", ([1, 0, 0, 0, 1, 0, 0, 0, 1], [0, 5, 0]), "test4")
add_terrain(world, "./data/cube.off", ([1, 0, 0, 0, 1, 0, 0, 0, 1], [5, 0, 0]), "test5")
add_terrain(world, "./data/cube.off", ([1, 0, 0, 0, 1, 0, 0, 0, 1], [0, -5, 0]), "test6")
add_terrain(world, "./data/cube.off", ([1, 0, 0, 0, 1, 0, 0, 0, 1], [-5, 0, 0]), "test7")

vis.add("world", world)
vis.show()

sim = klampt.Simulator(world)

lidar = sim.controller(0).sensor("lidar")
vis.add("lidar", lidar)

time.sleep(1)

def publish_gmapping_stuff(conn):
    rospy.init_node("sensing_test_child")
    pub = rospy.Publisher("base_scan", sensor_msgs.msg.LaserScan)

    ros_msg = None
    curr_pose_child = None

    while True:
        if conn.poll():
            ros_msg, curr_pose_child = conn.recv()

        if ros_msg is not None and curr_pose_child is not None:
            pub.publish(ros_msg)
            publish_tf(curr_pose_child)

        now = time.time()

parent_conn, child_conn = Pipe()
ros_process = Process(target=publish_gmapping_stuff, args=(child_conn, ))
ros_process.start()

rospy.init_node("sensing_test_parent")
start_time = time.time()
while True:
    lidar.kinematicSimulate(world, 0.01)
    print('running')
    ros_msg = ros.to_SensorMsg(lidar, frame="/base_scan")
    print('ran this command')
    curr_pose = robot.base_state.measuredPos
    parent_conn.send([ros_msg, curr_pose])

    vis.lock()
    if time.time() - start_time < 5:
        robot.setBaseVelocity([0.5, 0.1])
    else:
        robot.setBaseVelocity([0.0,0.5])
    vis.unlock()
    time.sleep(0.1)

ros_process.join()
vis.show()
