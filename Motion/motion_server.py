try:
	from SimpleXMLRPCServer import SimpleXMLRPCServer
except:
	from xmlrpc.server import SimpleXMLRPCServer
import signal
import sys
from motion import Motion
import time
import logging
from datetime import datetime
from trina_logging import get_logger
import numpy as np
filename = "errorLogs/logFile_" + datetime.now().strftime('%d%m%Y') + ".log"
logger = get_logger(__name__,logging.DEBUG,filename)


from xmlrpc.client import Marshaller
Marshaller.dispatch[np.float64] = Marshaller.dump_double
Marshaller.dispatch[np.ndarray] = Marshaller.dump_array

global robot
global server_started
global server_components

server_started = False

import traceback
from functools import wraps


def _runCommand(command):
	env = {'robot':robot, 'startServer':startServer,
		'restartServer':restartServer}
	exec('ret = ' + command)
	return ret


def startServer(mode, components, codename):
	global robot
	global server_started

	if server_started:
		logger.info("server is already activated")
		print("server already started ")
	else:
		robot = Motion(mode=mode, components=components, codename=codename)
		logger.info("%s mode is activated",robot.mode)
		server_started = True
		print("server started")
	return 0


def restartServer(mode="Kinematic", components=[], codename="seed"):
	global robot
	global server_started
	if(server_started):
		robot.shutdown()
	time.sleep(2)
	logger.info("Motion shutdown,restarting")
	robot = Motion(mode=mode, components=components, codename=codename)
	logger.info("%s mode is activated",robot.mode)
	server_started = True
	print("server started")
	return 0


def run_server_forever(ip_address,port):
	server = SimpleXMLRPCServer((ip_address,port), logRequests=False)
	server.register_introspection_functions()
	signal.signal(signal.SIGINT, sigint_handler)

	##add functions...
	server.register_function(_runCommand, 'runCommand')
	##
	print('#######################')
	print('#######################')
	logger.info("Server Created")
	print('Server Created')
	##run server
	server.serve_forever()

if __name__ == '__main__':
	import os,sys
	sys.path.append(os.path.expanduser("~/TRINA"))
	from Settings import trina_settings
	import argparse
	parser = argparse.ArgumentParser(description='Runs the motion server')
	parser.add_argument('-a','--ip', default='127.0.0.1', type=str, help='Server\'s IP address')
	parser.add_argument('-p','--port', default=trina_settings.motion_server_port(), type=int, help='Server\'s port number')
	parser.add_argument('--components', default=trina_settings.motion_server_components(), type=str, nargs='+', help='List of active components')
	parser.add_argument('--codename', default=trina_settings.robot_codename(), type=str, help="The robot model's codename")
	parser.add_argument('-m', '--mode', default=trina_settings.motion_server_mode(), type=str, help='The mode (Kinematic or Physical)')

	print()
	print("USAGE:")
	print()
	print("   motion_server.py [OPTIONS]")
	print()
	parser.print_help()
	args = parser.parse_args(sys.argv[1:])

	startServer(args.mode,args.components,args.codename)
	run_server_forever(args.ip,args.port)
