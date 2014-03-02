# -*- coding: utf-8 -*-

__author__ = 'Powell Molleti'
__version__ = '0.1.1'

"""Module for grade"""

# system imports
import os

# helper library imports
import yaml


class Grade:
    """Base implementation for grading code.

    Current implementation has the following restrictions
    test code input:
    1. Expects only single function for evaluation
    2. Return value is the only way to get results.
    3. Function arguments are of primitive types.

    Design:
      Use a yaml file as input that proves spec for evaluating code.
      Yaml file provides syntax and defines grading numbers and test
      data.

      This class is responsible for parsing the yaml and it tries to
      abstract evaluation steps and grading method from derived
      implementation.

    Yaml input spec:
    #-----------------------------------------------------------
    # spec to evaluate and grade the coding test
    #-----------------------------------------------------------

    # codespec gives us input on how to understand the code
    codespec:
     filesizelimit: 1           # in MB
     language: 'python'
     function: 'abbreviate_name'
     argcount: 2
     argnames:
      - full_name
      - abc
     argtypes:
      - string
      - integer
    returntype:
      - integer

    # evalspec gives us flexibility in grading various
    # eval points, like coding standards, bad code,
    # non-working code, each test case weight
    evalspec:
     grademax: 100             # Max grade possible
     wellness:
      convention:
       maxhit: 10              # Max deduction possible
       error: 1                # Deduction per error
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
     maxhit: 100              # Max deduction possible.
     count: 3                 # maxhit/count is each test weight.
     timeout: 0.5             # Max alloted exec time for each test.
     input:                   # Test case input, each line is one test run
      - [ 'John Smith', 1 ]
      - [ 'Anna Maria Simpson ', 2]
      - [ 'Bob Alan Faria Stewart ', 3]
     output:                  # Test output, each line is one test run
      - 1
      - 2
      - 5

    Following is how we grade the code:
    1. Complile to ensure it works. Scripts that cannot
       compiled will skip this implementation.
    2. Rate code by syntax, lack of comments etc.
    3. Run configured tests and rate based on results.

    """

    def __str__(self):
        return "grade"

    def __init__(self, config_spec, user_prog):
        """Initialize class members.

        Parameters:
          config_spec - Yaml spec for how to parse, grade.
          user_prog   - Given user code, has to be a single file.
          log_level   - default of DEBUG.

        """
        self.config_spec = config_spec
        self.user_prog = user_prog
        self.max_file_size = 10         # 10MB
        self.code_spec = None           # yaml load time
        self.eval_spec = None           # yaml load time
        self.language = ""
        self.max_grade = 'none'
        self.function_name = ""
        self.arg_count = 0
        self.arg_list = []
        self.arg_type_list = []
        self.return_type = 'bool'
        self.wellness_map = {}
        self.wellness_check_list = []
        self.timeout_interval = 1       # in Seconds max run time per test
        self.testcase_map = {}
        self.test_count = 0             # Default is no tests
        self.testcase_input = {}
        self.testcase_output = {}
        self.eval_result = 'none'
        self.grade_report = {}
        self.grade_yaml = {}
        self.logger = None

    def __load_config_spec(self, config_stream):
        """Loads the available yaml stream and populates
           the right data-structs

           TODO: This needs more spec checks? i.e reject a spec
           if something is missing.

           We do assume defaults for some items when not given.
        """
        data_map = None
        try:
            data_map = yaml.safe_load(config_stream)
        except Exception, e:
            self.logger.error("Loading yaml config_spec [%s]: %s" %
                              (self.config_spec, str(e)))
            return -1

        data_dump = yaml.dump(data_map)

        # populate our member variables
        for k, v in data_map.iteritems():
            if k == 'codespec':
                self.code_spec = v
                continue
            if k == 'evalspec':
                self.eval_spec = v
                continue

        if self.code_spec is None:
            self.logger.error("conf_spec[%s] does not contain 'codespec'" %
                              self.config_spec)
            return -1

        if self.eval_spec is None:
            self.logger.error("conf_spec[%s] does not contain 'evalspec'" %
                              self.config_spec)
            return -1

        if 'language' in self.code_spec.keys():
            self.language = self.code_spec['language']
        else:
            self.logger.error("conf_spec[%s] does not contain 'language'" %
                              self.config_spec)
            return -1

        if 'function' in self.code_spec.keys():
            self.function_name = self.code_spec['function']
        else:
            self.logger.error("conf_spec[%s] does not contain 'function'" %
                              self.config_spec)
            return -1

        if 'argcount' in self.code_spec.keys():
            self.arg_count = int(self.code_spec['argcount'])

        if self.arg_count > 0:
            # Parse only when arg_count > 0
            if 'argnames' in self.code_spec.keys():
                self.arg_list = self.code_spec['argnames']

                if 'argtypes' in self.code_spec.keys():
                    self.arg_type_list = self.code_spec['argtypes']

        if len(self.arg_list) != self.arg_count or \
           len(self.arg_list) != len(self.arg_type_list):
            self.logger.error('conf_spec[%s] parse error, arg count mismatch' %
                              (self.config_spec))
            return -1

        if 'returntype' in self.code_spec.keys():
            self.return_type = self.code_spec['returntype']

        if 'filesizelimit' in self.code_spec.keys():
            self.max_file_size = int(self.code_spec['filesizelimit'])

        if 'grademax' in self.eval_spec.keys():
            self.max_grade = int(self.eval_spec['grademax'])
        else:
            self.max_grade = 100

        if 'wellness' in self.eval_spec.keys():
            self.wellness_map = self.eval_spec['wellness']
            for k, v in self.wellness_map.iteritems():
                self.wellness_check_list.append(k)

        if 'testcases' in self.eval_spec.keys():
            self.testcase_map = self.eval_spec['testcases']
            if 'count' in self.testcase_map.keys():
                self.test_count = int(self.testcase_map['count'])

            if 'timeout' in self.testcase_map.keys():
                # time allotted per test run in seconds.
                self.timeout_interval = float(self.testcase_map['timeout'])

            for k, v in self.testcase_map.iteritems():
                if k == 'input':
                    self.testcase_input = v
                    continue
                if k == 'output':
                    self.testcase_output = v
                    continue

            if len(self.testcase_input) != self.test_count or \
               len(self.testcase_input) != len(self.testcase_output):
                errStr = 'conf_spec [%s] parse error, i/o mismatch' \
                         % (self.config_spec)
                self.logger.error(errStr)
                return -1

        self.logger.debug("max file size : %s MB" % self.max_file_size)
        self.logger.debug("yaml input: %s" % data_dump)

        return 0

    def __check_user_prog(self):
        """Check the size of user prog, it should not
           exceed the limit in config_spe

           Feel free to add more checks that do not try to do anything
           the derived classes will perform when evaluating the code.
        """
        file_size = os.stat(self.user_prog).st_size
        size_max_bytes = self.max_file_size * 1024 * 1024
        if file_size > size_max_bytes:
            self.logger.error("user_prog [%s] size %s bytes, ' + \
               'exceeded limit %s bytes" % (self.user_prog, str(file_size),
                                      size_max_bytes))
            return -1

        return 0

    def load(self):
        """Loads both the config_spec and checks for a valid
           user_prog.

           Populates various members for later.
        """

        # First open the yaml spec.
        fd = None
        try:
            fd = open(self.config_spec, 'r')
        except Exception, e:
            self.logger.error("Reading config_spec[%s]: %s" %
                              (self.config_spec, str(e)))
            return -1

        # Load all the data-structs that specify how to
        # evalulate the code.
        if self.__load_config_spec(fd) < 0:
            fd.close()
            return -1

        fd.close()
        fd = None
        # Try opening the user program.
        try:
            fd = open(self.user_prog, 'r')
        except Exception, e:
            self.logger.error("Reading user_prog[%s]: %s" %
                              (self.user_prog, str(e)))
            return -1

        self.logger.info("Successfully Loading config_spec[%s]" %
                         self.config_spec)

        # Run few basic checks on the user_prog
        if self.__check_user_prog() < 0:
            fd.close()
            return -1

        fd.close()
        self.logger.info("Valid user_prog[%s], using for furthuer evaluation" %
                         self.user_prog)

        # Now that we parsed the yaml and know have a valid user file
        # upate our report.
        self.grade_report['function'] = self.function_name
        self.grade_report['filename'] = self.user_prog
        self.grade_report['language'] = self.language

        return 0

    def grade_wellness(self, wellness_data):
        """Get the user program wellness data and input from config
           spec. With both the info adjust the grade and return.

           Parameters:
           wellness_data - input containing wellness data.
             Each category should contain items. We do not need to
             understand the items. The fact that there is an item is
             considered as an issue. So deduct the grade accordingly.
        """

        for k, v in self.wellness_map.iteritems():
            if k in wellness_data.keys():
                items = wellness_data[k]
                maxhit = int(v['maxhit'])
                errcut = int(v['error'])

                total_errhit = errcut * len(items)
                grade_adj = min(maxhit, total_errhit)

                if self.eval_result > grade_adj:
                    self.eval_result = self.eval_result - grade_adj
                else:
                    self.eval_result = 0      # 0%!!!!

        return 0

    def grade_testrun(self, testrun_data):
        """Get the user program testrun data and input from config
           spec. With both the info adjust the grade and return.

           Parameters:
           testrun_data - input containing testrun data.
           Example of testrun_data:
             [ 'fail' , 'FAILED - Expected : 1 - Received : 'Tony' ]
             [ 'pass', 'PASSED - Expected : 'Tony - Received 'Tony' ]

           We have three category of test result:
           1. 'pass' - Test case passed so do not decrement grade.
           2. 'fail' - Test case failed so decrement grade.
           3. 'none' - Operation issue do not decrement grade.
        """

        maxhit = 100  # Default, Typically test cases failures can
                      # get you 0%
        # grab from spec if available.
        if 'maxhit' in self.testcase_map.keys():
            maxhit = int(self.testcase_map['maxhit'])

        # make sure we got the count right
        if self.test_count == 0:
            self.logger.info('No test cases to evalulate bail!')
            return 0

        if len(testrun_data) < self.test_count:
            self.logger.error('Testrun data dount [%s] is less than ' +
                              'expected count [%s]' %
                              (len(testrun_data), self.test_count))
            return -1

        errhit = float(maxhit)/self.test_count

        for items in testrun_data:
            if 'fail' == items[0]:
                if self.eval_result > errhit:
                    self.eval_result = self.eval_result - errhit
                else:
                    self.eval_result = 0
                    break                 # done decrementing

        return 0

    def check_function_def(self):
        """Has to be implemented in derived class!!!"""

        self.logger.info("check_function_def: Not implemented in base class!")
        return -1

    def run_compile_test(self):
        """If the code cannot be compiled then we skip this section"""

        self.logger.info("run_compile_test: Cannot compile this code, " +
                         "skipping!")
        return 0

    def run_wellness_check(self):
        """Has to be implemented in derived class!!!"""

        self.logger.info("run_wellness_check: Not implemented in base class!")
        return -1

    def run_test_cases(self):
        """This helper hands off this work to the derived class!"""

        self.logger.info("run_test_cases: Not implemented in base class!")
        return -1

    def eval_user_prog(self):
        """Implemented here, defines basic structure on how to evaluate
           the code. Free to override in derived class, but if this works
           then less work for u!!

           Following is the implementation steps:
           1. Run parse check, if fails return and set eval_result to 0
           2. Run compile check, if fails return and set eval_result to 0
           3. Run code health/wellness check, fails only for operational error
           4. Run test cases, fails only for operation error.
        """

        self.eval_result = self.max_grade
        retval, retstr = self.check_function_def()
        self.grade_report['parsecheck'] = {'status': 'pass',
                                           'output': retstr}
        if retval < 0:
            self.grade_report['parsecheck'] = {'status': 'fail',
                                               'output': retstr}
            # if we could not parse then no go!.
            self.eval_result = 0
            return -1

        # if we reached here then we can move on to try to compile, check
        # for better codeness and then move to test case run.
        retval, retstr = self.run_compile_test()
        self.grade_report['compile'] = {'status': 'pass',
                                        'output': retstr}
        if retval < 0:
            # If compile fails then we do not grade.
            self.grade_report['compile'] = {'status': 'fail',
                                            'output': retstr}
            # if we could not compile then no go!.
            self.eval_result = 0
            return -1

        # Check for how well the code is written now that it
        # compiled ok!
        retval, retdata = self.run_wellness_check()
        self.grade_report['wellness'] = retdata
        if retval < 0:
            # something went wrong
            # Some operation error?
            self.eval_result = 'None'
            return -1

        # Look at the wellness report and adjust the grade
        # accordingly.
        self.grade_wellness(retdata)

        retval, retdata = self.run_test_cases()
        self.grade_report['testrun'] = retdata
        if retval < 0:
            # something went wrong
            return -1

        # Now grade the test run
        self.grade_testrun(retdata)

        return 0

    def print_line(self, size=50):
        """Print line with char '-' on console, default length to
           print is 50.
        """
        print ('%s' % ('-'*size))

    def compile_grade_report(self):
        """Now that we have details publish them.
           Generate and save the yaml file in test program directory.
           Print a nice report to console.
        """

        # Store the grade result in 10/100, 65.7/200 etc
        eval_str = ""
        if type(self.eval_result) is str:
            eval_str = self.eval_result
        else:
            eval_str = str(round(self.eval_result, 2))

        eval_out = ""
        if type(self.max_grade) is str:
            eval_out = 'None'
        else:
            eval_out = eval_str + '/' \
                                     + str(round(self.max_grade, 2))

        self.grade_report['grade'] = eval_out

        self.grade_yaml['report'] = self.grade_report

        fpath, fonly = os.path.split(self.user_prog)
        fgrade_report = fpath + '/' + 'grade_report_' + \
                        fonly.split('.')[0] + '.yaml'

        with open(fgrade_report, 'w') as outfile:
            outfile.write(yaml.dump(self.grade_yaml, default_flow_style=True))

        self.print_line()
        print ('Report')
        self.print_line()
        if 'filename' in self.grade_report.keys():
            print ('Filename : ' + self.grade_report['filename'])
        if 'language' in self.grade_report.keys():
            print ('Language : ' + self.grade_report['language'])
        if 'function' in self.grade_report.keys():
            print ('Function : ' + self.grade_report['function'])
        if 'grade' in self.grade_report.keys():
            grade_result = self.grade_report['grade']
        else:
            grade_result = 'Not available'
        print ('Grade    : ' + grade_result)
        self.print_line()
        if 'parsecheck' in self.grade_report.keys():
            status = self.grade_report['parsecheck']
            print ('Parse Check    : ' + status['status'])
            print ('\tOutput : ' + status['output'])
            self.print_line()
        if 'compile' in self.grade_report.keys():
            status = self.grade_report['compile']
            print ('Compile Check  : ' + status['status'])
            print ('\tOutput : ' + status['output'])
            self.print_line()
        if 'wellness' in self.grade_report.keys():
            status = self.grade_report['wellness']
            print ('Wellness')
            for k, v in status.iteritems():
                print ("\t%s  :" % k)
                for i in v:
                    print ("\t\t%s" % v)
            self.print_line()
        if 'testrun' in self.grade_report.keys():
            status = self.grade_report['testrun']
            print ("Test Report")
            count = 1
            for item in status:
                i = item[1]
                print("\t%s" % ('-'*42))
                print("\tTest [%d], %s" % (count, i))
                count = count + 1
            self.print_line()

        return 0

    def run(self):
        """Main run method needs to be called to load, eval and report."""

        if self.load() == 0:
            # Run evalution only if we could load properly.
            self.eval_user_prog()
        self.compile_grade_report()

        return 0
