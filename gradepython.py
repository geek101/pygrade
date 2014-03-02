#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Module for Python implementation of Grade module."""

__author__ = 'Powell Molleti'
__version__ = '0.1.1'

# system imports
import sys
import os

# helper imports
import argparse
import logging
import re
import itertools
import py_compile
import subprocess
import time

# Base class import
from grade import Grade


class PyGrade(Grade):
    """Python implementation of Grade, here we implement language specific
       hooks that help with grading python code that is submitted by user

       Feature highlight:
       1. Function parser.
           We use regex to find the given function in user submitted code.
           We then check if the args are specified according to given spec.
       2. Compile test.
           We use py_compile module to compile given user code. This could
           be done via seperate process.
       3. Code quality check.
           Here we use 'pylint', with default configuration for now.
           'pylint' runs using given user code and we parse the output.
           'pylint' supports following various categories, There are 5
           kind of message types :
             * (C) convention, for programming standard violation
             * (R) refactor, for bad code smell
             * (W) warning, for python specific problems
             * (E) error, for much probably bugs in the code
             * (F) fatal, if an error occurred which prevented pylint from
                   doing further processing.
       4. Test case check.
           We take user program and generate new code with '__main__'
           method run desired test.
           This way we run the user program in a seperate process hence
           giving us ability monitor it, and also helps us make sure running
           user program does not impact our execution.

           TODO:  potentialy run it in a seperate sandbox/env, with
                  restricted privilidges.
    """

    def __str__(self):
        return "PyGrade"

    def __init__(self, config_spec, user_prog, log_level=logging.DEBUG):
        """Init method, initialize the super class and then set the
           logger

        Keyword arguments:
        config_spec -- Config yaml file.
        user_prog -- Give user code
        log_level -- Logger logging level, defaults to DEBUG
        """
        Grade.__init__(self, config_spec, user_prog)

        # Initialze logger
        self.logger = logging.getLogger(str(self))
        self.logger.setLevel(log_level)
        ch = logging.StreamHandler()
        ch.setLevel(log_level)
        formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def check_function_def(self):
        """Here we use good old regex, this is safe since we
           have determined that file size will not be infinite!

        TODO:
        1. Support for 'arg=10' etc is lacking.
        2. Support for *args, **keywords etc is lacking
        """

        # XXX: Copied the code from http://stackoverflow.com/\
        # questions/10158403/python-regex-for-python-function-signatures
        # TODO: will not work if any arg has the following 'a=10'
        # or *args etc.

        # Python identifiers start with a letter or _,
        # and continue with these or digits.
        FUNC_NAME = self.function_name
        IDENT = '[A-Za-z_][A-Za-z_0-9]*'

        # Commas between identifiers can have any amout of space on
        # either side.
        COMMA = '\s*,\s*'

        # Parameter list can contain some positional parameters.
        # For simplicity we ignore now named parameters, *args, and **kwargs.
        # We catch the entire list.
        PARAM_LIST = '\((' + IDENT + '?' + '(?:' + COMMA+IDENT + ')*' + ')?\)'

        # Definition starts with 'def', then identifier, some space,
        # and param list.
        DEF = 'def\s+(' + FUNC_NAME + ')\s*' + PARAM_LIST

        ident_rx = re.compile(IDENT)
        def_rx = re.compile(DEF)

        fd = None
        # Try opening the user program.
        try:
            fd = open(self.user_prog, 'r')
        except Exception, e:
            self.logger.error("Should not happen, Reading user_prog[%s]: %s" %
                              (self.user_prog, str(e)))
            return -1, str(e)

        # Try to find lines that match the function name,
        found = False
        for line in fd:
            match = def_rx.match(line)
            if match:
                name, paramlist = match.groups()
                # extract individual params
                params = [x.group()
                          for x in ident_rx.finditer(paramlist or '')]
                self.logger.info("Function found : %s %s" % (name, params))
                self.parsed_params = params
                found = True
                break

        if found is False:
            errStr = "Function not found : %s " % FUNC_NAME
            self.logger.info(errStr)
            return -1, errStr

        # We have the parameters in a list from parsing above, compare
        # that with what the config spec has.
        # TODO: May be we relax the strict order check?

        # Parameters typically wont be a large dataset unless this
        # is an attack.
        count = 0
        for x, y in itertools.izip(self.parsed_params, self.arg_list):
            if x != y:
                errStr = "Function arg mismatch for " + \
                         "parsed data: %s, spec data: %s" % (x, y)
                self.logger.info(errStr)
                return -1, errStr
            count = count+1

        if count != self.arg_count:
            errStr = "Function arg mismatch for " + \
                     "parsed data: %s, spec data: %s" % \
                     (self.parsed_params, self.arg_list)
            self.logger.info(errStr)
            return -1, errStr

        # The user function has more args than what we expected.
        # We cannot handle it for now.
        if len(self.parsed_params) > len(self.arg_list):
            errStr = "User code has more args than required " + \
                     "parsed data: %s, spec data: %s" % \
                     (self.parsed_params, self.arg_list)
            self.logger.info(errStr)
            return -1, errStr

        self.logger.info("Function args matched : %s , %s" %
                         (self.parsed_params, self.arg_list))
        return 0, ""

    def run_compile_test(self):
        """We do an inline compile, we could fork a process for this. It is
           highly unlikely we will encounter strings that can cause us to
           crash due to using python compile api(py_compile).

        Return values:
        pair -- -1/0, error string
        """

        try:
            py_compile.compile(self.user_prog, doraise=True)
        except Exception as e:
            self.logger.error("Failed to compile - %s - Error : %s" %
                              (self.user_prog, str(e)))
            return -1, str(e)

        self.logger.info("Compilation succeeded for  %s" % self.user_prog)
        return 0, ""

    def run_wellness_check(self):
        """We use pylint via subprocess and parse its output.
           We then return a nice of number of errors for each
           wellness type!

        Supported messages:
        C -- convention
        R -- refactor
        W -- warning
        E -- error
        F -- fatal

        Return values
        pair -- -1,0, list
        """
        PYLINT_ARGS = "pylint -f parseable -r n " + self.user_prog
        pylint_output = None
        e = None
        try:
            pylint_output = subprocess.check_output(PYLINT_ARGS,
                                                    stderr=subprocess.STDOUT,
                                                    shell=True)
        except subprocess.CalledProcessError as e:
            self.logger.info("pylint error [%s] : %s" %
                             (PYLINT_ARGS, str(e)))
            pylint_output = str(e.output)

        self.logger.info("pylint output [%s] : %s" %
                         (self.user_prog, pylint_output))

        #self.process_pylint_output(pylint_output)
        well_report = {}
        for w in self.wellness_check_list:
            well_report[w] = []

        well_report['fatal'] = []
        option = {'[C': 'convention',
                  '[R': 'refactor',
                  '[W': 'warning',
                  '[E': 'error',
                  '[F': 'fatal', }

        onehit = 0
        for s in pylint_output.split('\n'):
            filestr = '^' + self.user_prog
            filestr_rx = re.compile(filestr)
            match = filestr_rx.match(s)
            if match is None:
                continue
            onehit = onehit + 1
            swords = s.split(' ')
            s2 = swords[1]
            s2 = s2[0] + s2[1]
            matched = option[s2]
            well_report[matched].append(s)
            self.logger.debug("output line : %s, %s" % (matched, s))

        # No errors and exception?, push the error to 'fatal' tag
        if onehit == 0 and e is not None:
            well_report['fatal'] = str(e)

        return 0, well_report

    def run_exec_test(self, exec_fname):
        """This function executes the python wrapper code which includes the
           user code. This code is run in a seperate process using
           subprocess.popen(). This helps us montior the process. We will
           kill the process if it exceeds its time limit for executing and
           mark the test as failed.

           TODO: Run the generated code in a seperate sandbox with
                 given priviledge restriction.

        Following are the features:
        1. Sends in the args with right type, position and data.
        2. Ensures return data type mathes with spec and what prog returned
        3. Catch crash and fails the test case.
        4. We compile our generated code first to make sure there is no
           operational error.

        Keyword arguments:
        exec_fname - filename of the executable.

        Return values:
        pair - -1/0, [ 'pass'/'fail'/'none', 'error_string' ]
        """

        p = None
        fname = ["/usr/bin/python", exec_fname]
        try:
            p = subprocess.Popen(fname, stderr=subprocess.STDOUT,
                                 stdout=subprocess.PIPE,
                                 close_fds=True)
        except Exception as e:
            self.logger.info("Popen error [%s] : %s" %
                             (fname, str(e)))

            return -1, ['none', str(e)]

        # How many times to poll for process status
        max_retry = 4

        # Get sleep interval in milliseconds.
        sleep_interval = float(self.timeout_interval) / max_retry

        count = 0
        p_returncode = None
        while count < max_retry:
            p.poll()
            p_returncode = p.returncode
            if p.returncode is not None:
                # subprocss has termiated
                break
            time.sleep(sleep_interval)
            count = count+1

        # If we are here due to count exceeded then kill the
        # process and return error.
        if count == max_retry:
            errStr = 'Test run exceeded timeout : %s' % self.timeout_interval
            self.logger.error(errStr)
            p.kill()
            p.wait()
            return 0, ['fail', errStr]

        # Check the return code for < 0 if the process was killed
        # someone else or died due to bad code!
        if p_returncode < 0:
            errStr = 'Process died with signal : %s' % abs(p_returncode)
            self.logger.error(errStr)
            # Whose fault is it?
            return -1, ['fail', errStr]

        # Get the program output and check if the test passed/failed
        stdoutdata, stderrdata = p.communicate()
        self.logger.info('Test result : \n \t[ %s , %s , returncode %s]' %
                         (stdoutdata, stderrdata, p_returncode))

        # Parse the stdoutdata so we know if test passed or failed.
        # Capture the reason.
        if p_returncode == 0:
            # Check if we have the 'PASSED - Expected :' value
            passstr = '^PASSED -'
            pass_rx = re.compile(passstr)
            match = pass_rx.match(stdoutdata)
            if match is None:
                return 0, ['fail', stdoutdata]

            return 0, ['pass', stdoutdata]

        # p_returncode == 1
        failstr = '^FAILED -'
        fail_rx = re.compile(failstr)
        match = fail_rx.match(stdoutdata)
        if match:
            return 0, ['fail', stdoutdata]

        self.logger.info('Test result is unknown!')
        # Should we count this towards grading?
        return 0, ['none', stdoutdata]

    def run_test_cases(self):
        """We get all the test suite that needs to be executed. We do this
           so that specific implementation can do more?.

           Should only return 'pass', 'none' or 'pass' so super can
           understand if a test case passed or failed.

        Return Value:
        pair - -1/0, [ [ 'string1', 'string2' ] ]

        Return List example:
             - [ 'fail', 'Killed due to timeout' ]
             - [ 'none', 'error Popen' ]
             - [ 'pass', 'PASSED - ...' ]
        """
        fpath, fonly = os.path.split(self.user_prog)
        exec_fname = fpath + '/' + 'exec_' + fonly
        self.logger.info('Using exec file : %s' % exec_fname)

        # we will grab the input code which is right now a function and
        # output with a main function and a set of args with right types.
        # We do this for every test run and collect the result and
        # convert the result to right type as per config_spec

        # This result is then used by the base implementation to grade
        # the code.

        # import <userprog without .py>
        INPUT_IMPORT_NAME = fonly.split('.')[0]

        # Given function name, we know this has been verified already
        FUNCTION_NAME = self.function_name

        CODE_PREFIX = "#!/usr/bin/env python\n\n" + \
                      "# import our dependencies only!\n" + \
                      "import sys\n" + \
                      "import traceback\n\n" + \
                      "# importing user code\n" + \
                      "import " + INPUT_IMPORT_NAME + '\n\n' + \
                      "if __name__ == \'__main__':\n" + \
                      "\targs = sys.argv[1:]\n\targs_right = []\n"

        # we need to take the input args and then generate code that will
        # convert them to right type and ad them to "args_right" list
        test_eval_data = []
        arg_cast = {'string': 'str',
                    'integer': 'int',
                    'float': 'float',
                    'bool': 'bool',
                    'double': 'double',
                    'complex': 'complex',
                    'none': 'None'}

        for tinput, toutput in itertools.izip(self.testcase_input,
                                              self.testcase_output):
            arg_position = 0
            ARG_CONVERSION = ""
            if tinput is None:
                FUNCTION_ARGS = '()'
            else:
                for t in tinput:
                    # Get the arg type from config_spec which helps
                    # us with sending right params to the test user
                    # function.
                    arg_type = self.arg_type_list[arg_position]

                    ARG_CONV_STR = '\targs_right.append(' + \
                                   arg_cast[arg_type] + \
                                   '(\'' + str(t) + '\')' + ')'
                    ARG_CONVERSION += ARG_CONV_STR + '\n'
                    arg_position = arg_position + 1
                FUNCTION_ARGS = '(*args_right)'

            CODE_CALL_FUNC = '\ttry:\n' + \
                             '\t\treturn_val = ' + INPUT_IMPORT_NAME + '.' + \
                             FUNCTION_NAME + FUNCTION_ARGS + '\n' + \
                             '\texcept Exception as e:\n' + \
                             '\t\texc_type, exc_value, exc_traceback ' + \
                             '= sys.exc_info()\n' + \
                             '\t\tprint (\"FAILED - STACKTRACE: \")\n' + \
                             '\t\ttraceback.print_exception(exc_type, ' + \
                             'exc_value, exc_traceback, limit=2, ' + \
                             'file=sys.stdout)\n' + \
                             '\t\tsys.exit(1)\n'

            # test case output is a single value! is our current
            # assumption!.
            if arg_cast[self.return_type[0]] == 'None':
                ARG_CAST = 'None\n'
            else:
                ARG_CAST = arg_cast[self.return_type[0]] + \
                           '(\'' + str(toutput) + '\')\n'

            RETURN_DATA = '\treturn_data = ' + ARG_CAST

            RETURN_VAL_CHECK = '\tif type(return_val) is not ' + \
                               'type(return_data):\n' + \
                               '\t\tprint (\"FAILED - Expected Return ' + \
                               'Type: %s' + \
                               ' - Received Return Type : %s \" %\n' + \
                               '\t\t  (type(return_data), ' + \
                               'type(return_val)))\n' + \
                               '\t\tsys.exit(1)\n' + \
                               '\tif return_val != return_data:\n' + \
                               '\t\tprint (\"FAILED - Expected : %s' + \
                               ' - Received : %s \" %\n' + \
                               '\t\t  (return_data, ' + \
                               'return_val))\n' + \
                               '\t\tsys.exit(1)\n'

            CODE_EXIT = '\tprint (\"PASSED - Expected : %s' + \
                        ' - Received : %s \" %\n' + \
                        '\t\t(return_data, return_val))\n' + \
                        '\tsys.exit(0)\n'
            CODE_GEN = CODE_PREFIX + ARG_CONVERSION + CODE_CALL_FUNC + \
                RETURN_DATA + RETURN_VAL_CHECK + CODE_EXIT

            # Ok CODE_GEN has the generated code.
            # Output this to a temporary file and then lets run it
            # in a seperate process.
            self.logger.debug('\n%s' % CODE_GEN)

            fd = None
            try:
                fd = open(exec_fname, 'w')
            except Exception, e:
                self.logger.error("Creating exec file[%s]: %s" %
                                  (exec_fname, str(e)))
                # This is a fatal error, should not impact grading?
                return -1, test_eval_data

            # Write the generated code.
            fd.write(CODE_GEN)

            # Close the file
            fd.close()

            # Ensure that this code compiles!, we did confirm that
            # user provided code compiles so our additions should
            # compile.
            # TODO: Have to make sure user does not have his own
            # __main__ ?
            try:
                py_compile.compile(exec_fname, doraise=True)
            except Exception as e:
                self.logger.error("Failed to compile - %s - Error : %s" %
                                  (exec_fname, str(e)))
                return -1, test_eval_data

            retval, retargs = self.run_exec_test(exec_fname)
            self.logger.debug('retval %s , retargs %s' %
                             (retval, retargs))

            test_eval_data.append(retargs)

            # error < 0 means a fatal problem bail!
            if retval < 0:
                return -1, test_eval_data

        # Return the test run evaluation.
        return 0, test_eval_data


def main(argv):
    """Parse the args and initialize the grade class.
       Calls grade->run() which does everything one needs!.

    Keyword arguments:
    argv - user args.
    """

    usage = '%(prog)s -s <yaml spec> -u <user program file> ' + \
            '[ -v <my version> -x <log verbose level> ]'
    description = 'Python function grader tool.'
    parser = argparse.ArgumentParser(usage=usage, description=description)

    parser.add_argument('-s', '--spec', action='store',
                        nargs=1, dest='configSpecFileName',
                        help='Input spec for valuating user program',
                        metavar="configSpecFileName", required=True)

    parser.add_argument('-u', '--uprog', action='store',
                        nargs=1, dest='userProgFileName',
                        help='User program file',
                        metavar="userSpecFileName", required=True)

    parser.add_argument('-x', '--verbose', action='count',
                        help='Logging verbosity')

    parser.add_argument('-v', '--version', action='version',
                        help='Show verion', version='1.01')

    try:
        args = parser.parse_args()
    except SystemExit:
        return -1

    # we have the args.
    py_grade = PyGrade(args.configSpecFileName[0], args.userProgFileName[0],
                       logging.WARN)
    py_grade.run()


if __name__ == "__main__":
    main(sys.argv[1:])
