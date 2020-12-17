from xmlrpc.client import ServerProxy
from threading import Thread, Lock
import threading
import time
from klampt import WorldModel
import os
import numpy as np
from Utils import parseCommand
dirname = os.path.dirname(__file__)
#getting absolute model name
model_name = os.path.join(dirname, "data/TRINA_world_seed.xml")

class MotionClient:
	def __init__(self, address = 'http://127.0.0.1:8000'):
		self.s = ServerProxy(address)
		self.shut_down = False

	def send_command(self, command):
		return self.s.run_command(command)

if __name__=="__main__":
	motion = MotionClient('http://localhost:8080')
	motion.send_command(parseCommand('startServer', 'Kinematic',
		['right_limb','left_limb'], 'bubonic'))
	motion.send_command('robot.startup')
	time.sleep(0.05)
	print(motion.send_command('sensedLeftEEWrench'))
	motion.send_command('robot.shutdown')
