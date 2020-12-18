import sys
if sys.version_info[0] >= 3:
	from xmlrpc.client import ServerProxy
else:
	from xmlrpclib import ServerProxy
from threading import Thread, Lock
import threading
import time
from klampt import WorldModel
import os
import numpy as np
from Utils import parseCommand
try:
	from Settings import trina_settings
except ImportError:
	sys.path.append(os.path.expandpath("~/TRINA"))
	from Settings import trina_settings

class MotionClient:
	def __init__(self, address = 'auto'):
		if address == 'auto':
			address = trina_settings.motion_server_addr()
		self.s = ServerProxy(address)
		self.shut_down = False

	def sendCommand(self, command):
		return self.s.runCommand(command)

if __name__=="__main__":
	motion = MotionClient('http://localhost:8080')
	motion.sendCommand(parseCommand('startServer', 'Kinematic',
		['right_limb','left_limb'], 'bubonic'))
	motion.sendCommand('robot.startup')
	time.sleep(0.05)
	print(motion.sendCommand('robot.sensedLeftEEWrench'))
	motion.sendCommand('robot.shutdown')
