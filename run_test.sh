#! /bin/bash

./gradepython.py -s test/code_spec.yaml -u test/test.py > test.report
./gradepython.py -s test1/code_spec.yaml -u test1/test.py > test1.report
./gradepython.py -s test2/code_spec.yaml -u test2/test.py > test2.report
./gradepython.py -s test3/code_spec.yaml -u test3/test.py > test3.report
./gradepython.py -s test4/code_spec.yaml -u test4/test.py > test4.report
./gradepython.py -s test5/code_spec.yaml -u test5/test.py > test5.report
./gradepython.py -s test6/code_spec.yaml -u test6/test.py > test6.report

cat test.report >> all.report
cat test1.report >> all.report
cat test2.report >> all.report
cat test3.report >> all.report
cat test4.report >> all.report
cat test5.report >> all.report
cat test6.report >> all.report


