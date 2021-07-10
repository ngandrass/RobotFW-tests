*** Settings ***
Documentation       Benchmark timeout operations.

# import libs and keywords
Resource            api_shell.keywords.txt
Resource            periph_timer_benchmarks.keywords.txt

# add default tags to all tests
Force Tags          periph_timer_benchmarks

Suite Setup         Run Keywords    Default Suite Setup
Test Setup          Run Keywords    Default Test Setup
Test Teardown       Run Keywords    Default Test Teardown

*** Keywords ***
Benchmark Absolute Timeouts
    [Arguments]  ${FREQ}  ${TICKS}  ${REPEATS}
    Run Keyword                 Default Benchmark Setup

    # Check arguments
    Should be True  ${REPEATS} <= 50  # Don't generate more events than PHiLIP trace can hold

    # Execute
    FOR  ${n}  IN RANGE  ${REPEATS}
        API Call Should Succeed     Bench Absolute Timeout  ${FREQ}  ${TICKS}
    END

    # Evaluate
    API Call Should Succeed     PHILIP.Read Trace
    Record Property             trace  ${RESULT['data']}

    ${BENCH_RESULT} =           Process Bench Absolute Timeout  ${RESULT['data']}
    Record Property             frequency                       ${FREQ}
    Record Property             ticks                           ${TICKS}
    Record Property             repeats                         ${REPEATS}
    Record Property             bench_absolute_timeouts         ${BENCH_RESULT}

*** Test Cases ***

###################
## 1 us Timeouts ##
###################

Benchmark Absolute Timeouts 10@10MHz
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  10000000   10      50

####################
## 10 us Timeouts ##
####################

Benchmark Absolute Timeouts 100@10MHz
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  10000000   100     50

Benchmark Absolute Timeouts 10@1MHz
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  1000000    10      50

#####################
## 100 us Timeouts ##
#####################

Benchmark Absolute Timeouts 1000@10MHz
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  10000000   1000    50

Benchmark Absolute Timeouts 100@1MHz
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  1000000    100     50

Benchmark Absolute Timeouts 10@100kHz
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  100000     10      50

###################
## 1 ms Timeouts ##
###################

Benchmark Absolute Timeouts 10000@10MHz
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  10000000   10000   50

Benchmark Absolute Timeouts 1000@1MHz
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  1000000    1000    50

Benchmark Absolute Timeouts 100@100kHz
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  100000     100     50

Benchmark Absolute Timeouts 10@10kHz
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  10000      10      50

####################
## 10 ms Timeouts ##
####################

Benchmark Absolute Timeouts 100000@10MHz
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  10000000   100000  50

Benchmark Absolute Timeouts 10000@1MHz
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  1000000    10000   50

Benchmark Absolute Timeouts 1000@100kHz
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  100000     1000    50

Benchmark Absolute Timeouts 100@10kHz
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  10000      100     50

#####################
## 100 ms Timeouts ##
#####################

Benchmark Absolute Timeouts 1000000@10MHz
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  10000000   1000000     50

Benchmark Absolute Timeouts 100000@1MHz
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  1000000    100000      50

Benchmark Absolute Timeouts 10000@100kHz
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  100000     10000       50

Benchmark Absolute Timeouts 1000@10kHz
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  10000      1000        50

##################
## 1 s Timeouts ##
##################

Benchmark Absolute Timeouts 10000000@10MHz
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  10000000   10000000    50

Benchmark Absolute Timeouts 1000000@1MHz
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  1000000    1000000     50

Benchmark Absolute Timeouts 100000@100kHz
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  100000     100000      50

Benchmark Absolute Timeouts 10000@10kHz
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  10000      10000       50
