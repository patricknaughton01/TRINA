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
server_started = False

ip_address = 'localhost'
port = 8080

def sigint_handler(signum,frame):
	global robot
	global server_started
	if server_started:
		robot.shutdown()
	sys.exit(0)

server = SimpleXMLRPCServer((ip_address,port), logRequests=False)
server.register_introspection_functions()
signal.signal(signal.SIGINT, sigint_handler)

import traceback
from functools import wraps

def xmlrpcMethod(name):
    """
    Decorator that registers a function to the xmlrpc server under the given name.
    """
    def register_wrapper(f):
        server.register_function(f, name)
        return f
    return register_wrapper

def loggedMethod(f):
    """
    Decorator that adds stack trace dumping (stdout and logger) to a function.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(tb)
            print(tb)
            raise e
    return wrapper

@xmlrpcMethod("runCommand")
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

print('#######################')
print('#######################')
logger.info("Server Created")
print('Server Created')
##run server
server.serve_forever()
