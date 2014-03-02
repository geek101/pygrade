#!/usr/bin/env python

# import our dependencies only!
import sys
import time
import traceback

# importing user code
import test

if __name__ == '__main__':
	args = sys.argv[1:]
	args_right = []
	args_right.append(str('Bob Alan Faria Stewart '))
        try:
                return_val = test.abbreviate_name(*args_right)
        except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print ("FAILED - STACKTRACE: ")
                traceback.print_exception(exc_type, exc_value, exc_traceback,
                                          limit=2, file=sys.stdout)
                #import pdb; pdb.set_trace()
                sys.exit(0)
	return_data = str('B. A. F. Stewart')
	if return_val != return_data:
		print ("FAILED - Expected : %s - Recieved : %s " %
		  (return_data, return_val))
		sys.exit(1)
	print ("PASSED - Expected : %s - Recieved : %s " %
		(return_data, return_val))
	sys.exit(0)
