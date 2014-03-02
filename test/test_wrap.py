#!/usr/bin/env python

import sys

import test

if __name__ == '__main__':
    args = sys.argv[1:]
    args_right = []
    v1 = str(args[0])
    args_right.append(v1)
    v2 = int(args[1])
    args_right.append(v2)
    import pdb;pdb.set_trace()
    print test.abbreviate_name(*args_right)
