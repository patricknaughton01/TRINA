""" this file servers both as a camera server and a logger"""
import sys
import signal
sys.path.append('../../')
from SensorModule import Camera_Robot
sys.path.append('../../Motion/')
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from threading import Thread, Lock, RLock
import threading
import time
import numpy as np
sys.path.remove('/opt/ros/kinetic/lib/python2.7/dist-packages')
import cv2
sys.path.append('/opt/ros/kinetic/lib/python2.7/dist-packages')
from motion_client_python3 import MotionClient

from utils import *
class CalibrationLogger:
    def __init__(self,cameras,motion_address,codename):
        self.camera = Camera_Robot(robot = [],world = [], cameras = cameras,ros_active = False, use_jarvis = False, mode = 'Physical')
        self.robot =  MotionClient(address = motion_address)
        self.robot.startServer(mode = 'Physical',components = ['left_limb','right_limb'],codename = codename)
        self.robot.startup()
        self.shutdown_flag = False
        self.pics = []
        self.camera_dt = 0.2
        self.system_start_time = time.time()
        self._lock = RLock()
        self.init_move_time = 20.0
        self.dt = 0.01
        self.cameras = cameras

    def collect(self,ref_traj,save_path):
        #move the arm to trajectory initial configuration
        left_q,right_q = extractLimbPositions(ref_traj.eval(0.0))
        self.robot.setLeftLimbPositionLinear(left_q,self.init_move_time)
        self.robot.setRightLimbPositionLinear(right_q,self.init_move_time)
        self.save_path = save_path
        time.sleep(self.init_move_time + 0.5)

        #start logging the pictures and robot state
        loggingThread = threading.Thread(target = self._cameraLoggingLoop)
        loggingThread.start()
        time.sleep(2)

        end_time = ref_traj.endTime()
        current_time = 0.0
        while current_time < end_time:
            left_q,right_q = extractLimbPositions(ref_traj.eval(current_time))
            self.robot.setLeftLimbPosition(left_q)
            self.robot.setRightLimbPosition(right_q)

        self.shutdown()
        return
   
    def _cameraLoggingLoop(self):
        """
        The depth channel uses uint16, i.e. 0-65535
        The maximum depth of realsense is 1.5m
        
        Note that the depth frame returned by realsense is already in depth image format.
        The depth frame from zed is 2D numpy array of floats. Need to be converted.

        Arbitrarily set the max depth of zed to be 5
        """
        counter = -1
        fc = open(self.save_path + 'camera_stamps.txt','w')
        fr = open(self.save_path + 'robot_state.txt','w')
        img_format = '.png'
        while not self.shutdown_flag:
            loop_start_time = time.time()
            self._lock.acquire()
            self.res = self.camera.get_rgbd_images()
            self._lock.release()

            for cn in self.cameras:
                color_frame = self.res[cn][0]
                if cn[0:4] == 'real': #realsense camera color channels need to be adjusted
                    color = cv2.cvtColor(np.asarray(color_frame), cv2.COLOR_RGB2BGR)
                else:
                    color = np.asarray(color_frame)
                if counter >= 0:
                    cv2.imwrite(self.save_path + cn + '-' + str(counter).zfill(5)+img_format,color,)
                    elapsed_time = time.time() - loop_start_time
                    if elapsed_time < self.camera_dt:
                        time.sleep(self.camera_dt - elapsed_time)
                    else:
                        time.sleep(0.00001)
                    t = time.time() - self.system_start_time
                    fc.write(str(t) + '\n')
                    fc.write('\n')

                    #now log the robot state
                    fr.write(str(t)+' ')
                    q = self.robot.sensedLeftLimbPosition()
                    for ele in q:
                        fr.write(str(ele)+' ')
                    q = self.robot.sensedRightLimbPosition()
                    for ele in q:
                        fr.write(str(ele)+' ')
                    wrench = self.robot.sensedLeftEEWrench()
                    for ele in wrench:
                        fr.write(str(ele)+' ')
                    wrench = self.robot.sensedRightEEWrench()
                    for ele in wrench:
                        fr.write(str(ele)+' ')
                    fr.write('\n')
                    print('elapsed_time:',elapsed_time)
                counter += 1
                    
        fc.close()
        fr.close()
                    
    def shutdown(self):
        self._lock.acquire()
        self.shutdown_flag = True
        #self.camera.safely_close_all()
        self._lock.release()

if __name__=="__main__":
    os.mkdir(path)
    server = CalibrationLogger(cameras,motion_address,codename)
    server.collect(self,ref_traj,save_path)
    def sigint_handler(signum, frame):
        """ Catch Ctrl+C tp shutdown 
        """
        assert(signum == signal.SIGINT)
        server.shutdown()

    signal.signal(signal.SIGINT, sigint_handler) # catch SIGINT (ctrl-c)   
