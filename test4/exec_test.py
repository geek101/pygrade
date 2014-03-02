#!/usr/bin/env python

# import our dependencies only!
import sys
import traceback

# importing user code
import test

if __name__ == '__main__':
	args = sys.argv[1:]
	args_right = []
	try:
		return_val = test.abbreviate_name()
	except Exception as e:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		print ("FAILED - STACKTRACE: ")
		traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
		sys.exit(1)
	return_data = bool('True')
	if type(return_val) is not type(return_data):
		print ("FAILED - Expected Return Type: %s - Received Return Type : %s " %
		  (type(return_data), type(return_val)))
		sys.exit(1)
	if return_val != return_data:
		print ("FAILED - Expected : %s - Received : %s " %
		  (return_data, return_val))
		sys.exit(1)
	print ("PASSED - Expected : %s - Received : %s " %
		(return_data, return_val))
	sys.exit(0)
