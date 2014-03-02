pygrade
=======

Grade python code , currently supports only python function as an input. Evaluation is controlled by YAML configuration. Uses pylint for grading.

TODO:
-----

Improve control of pylint via the yaml to adjust for trivial warnings
and errors.


How to run
==========

Step 1
------

You will need to have a python function that needs to be graded ofcourse.

Example:

"""
Keep pylint happy!
"""

def abbreviate_name(full_name):
    """
    abc
    """

    # split full name into invididual names
    names = full_name.split()
    abbrev_name = ""

    for index , name in enumerate(names):
        if index == 0:
            abbrev_name += name + " "
        else:
            abbrev_name += name[0] + ". "

    return abbrev_name


Step 2
------

Create an yaml to grade it, most of the yaml items are obvious.


#-----------------------------------------------------------
# spec to evaluate and grade the coding test
#-----------------------------------------------------------

# codespec gives us input on how to understand the code
codespec:
  filesizelimit: 1           # in MB
  language: 'python'
  function: 'abbreviate_name'
  argcount: 1
  argnames:
    - full_name
  argtypes:
    - string
  returntype:
    - string

# evalspec gives us flexibility in grading various
# eval points, like coding standards, bad code,
# non-working code, each test case weight
evalspec:
  grademax: 100
  wellness:
    convention:
      maxhit: 10
      error: 1
    refactor:
      maxhit: 20
      error: 2
    warning:
      maxhit: 100
      error: 10
    error:
      maxhit: 100
      error: 20
  testcases:
    maxhit: 100
    count: 3
    timeout: 2
    input:
      - [ 'John Smith']
      - [ 'Anna Maria Simpson ']
      - [ 'Bob Alan Faria Stewart ']
    output:
      - 'John S. '
      - 'Anna M. S. '
      - 'Bob A. F. S. '


Usage example:
./gradepython.py -s test1/code_spec.yaml -u test1/test.py

Output
======


--------------------------------------------------
Report
--------------------------------------------------
Filename : test1/test.py
Language : python
Function : abbreviate_name
Grade    : 99.0/100.0
--------------------------------------------------
Parse Check    : pass
	Output :
--------------------------------------------------
Compile Check  : pass
	Output :
--------------------------------------------------
Wellness
	fatal  :
	warning  :
	error  :
	refactor  :
	convention  :
		['test1/test.py:14: [C0326(bad-whitespace), ] No space allowed before comma']
--------------------------------------------------
Test Report
	------------------------------------------
	Test [1], PASSED - Expected : John S.  - Received : John S.

	------------------------------------------
	Test [2], PASSED - Expected : Anna M. S.  - Received : Anna M. S.

	------------------------------------------
	Test [3], PASSED - Expected : Bob A. F. S.  - Received : Bob A. F. S.

--------------------------------------------------



