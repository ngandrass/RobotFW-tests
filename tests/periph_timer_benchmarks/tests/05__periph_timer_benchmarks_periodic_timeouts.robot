*** Settings ***
Documentation       Benchmark periodic timeout operations.

# import libs and keywords
Resource            api_shell.keywords.txt
Resource            periph_timer_benchmarks.keywords.txt

# add default tags to all tests
Force Tags          periph_timer_benchmarks

Suite Setup         Run Keywords    Default Suite Setup
Test Setup          Run Keywords    Default Test Setup
Test Teardown       Run Keywords    Default Test Teardown

######### DEBUG START ##########
#*** Variables ***
#${TEST_REPEAT_TIMES}    1
#########  DEBUG END  ##########

*** Keywords ***
Benchmark Periodic Timeouts
    [Arguments]  ${FREQ}  ${TICKS}  ${CYCLES}  ${REPEATS}
    Run Keyword                 Default Benchmark Setup

    # Check arguments
    Should be True  ${REPEATS} <= 50  # Don't generate more events than PHiLIP trace can hold

    # Execute
    FOR  ${n}  IN RANGE  ${REPEATS}
        API Call Should Succeed Or Skip  Bench Periodic Timeout  ${FREQ}  ${TICKS}  ${CYCLES}
    END

    # Evaluate
    API Call Should Succeed     PHILIP.Read Trace
    Record Property             trace  ${RESULT['data']}

    ${BENCH_RESULT} =           Process Bench Periodic Timeout  ${RESULT['data']}
    Record Property             frequency                       ${FREQ}
    Record Property             ticks                           ${TICKS}
    Record Property             cycles                          ${CYCLES}
    Record Property             repeats                         ${REPEATS}
    Record Property             bench_periodic_timeouts         ${BENCH_RESULT}

*** Test Cases ***

#########################################
## Timeouts based on ${%{TIMER_SPEED}} ##
#########################################
Benchmark Periodic Timeouts 1x 1000@TIMER_SPEED
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  ${%{TIMER_SPEED}}  1000     1      50

Benchmark Periodic Timeouts 10x 1000@TIMER_SPEED
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  ${%{TIMER_SPEED}}  1000     10     50

Benchmark Periodic Timeouts 100x 1000@TIMER_SPEED
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  ${%{TIMER_SPEED}}  1000     100    50

Benchmark Periodic Timeouts 1000x 1000@TIMER_SPEED
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  ${%{TIMER_SPEED}}  1000     1000   50

Benchmark Periodic Timeouts 10x 10000@TIMER_SPEED
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  ${%{TIMER_SPEED}}  10000    10     50

Benchmark Periodic Timeouts 10x 100@TIMER_SPEED
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  ${%{TIMER_SPEED}}  100      10     50


###################
## 1 us Timeouts ##
###################

Benchmark Periodic Timeouts 10x 10@10MHz
    Skip If  ${%{BENCH_ADDITIONAL_TIMER_FREQUENCIES}} != 1  Additional timer frequency benchmarks disabled
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  10000000   10      10  5

####################
## 10 us Timeouts ##
####################

Benchmark Periodic Timeouts 10x 100@10MHz
    Skip If  ${%{BENCH_ADDITIONAL_TIMER_FREQUENCIES}} != 1  Additional timer frequency benchmarks disabled
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  10000000   100     10  5

Benchmark Periodic Timeouts 10x 10@1MHz
    Skip If  ${%{BENCH_ADDITIONAL_TIMER_FREQUENCIES}} != 1  Additional timer frequency benchmarks disabled
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  1000000    10      10  5

#####################
## 100 us Timeouts ##
#####################

Benchmark Periodic Timeouts 10x 1000@10MHz
    Skip If  ${%{BENCH_ADDITIONAL_TIMER_FREQUENCIES}} != 1  Additional timer frequency benchmarks disabled
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  10000000   1000    10  5

Benchmark Periodic Timeouts 10x 100@1MHz
    Skip If  ${%{BENCH_ADDITIONAL_TIMER_FREQUENCIES}} != 1  Additional timer frequency benchmarks disabled
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  1000000    100     10  5

Benchmark Periodic Timeouts 10x 10@100kHz
    Skip If  ${%{BENCH_ADDITIONAL_TIMER_FREQUENCIES}} != 1  Additional timer frequency benchmarks disabled
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  100000     10      10  5

###################
## 1 ms Timeouts ##
###################

Benchmark Periodic Timeouts 10x 10000@10MHz
    Skip If  ${%{BENCH_ADDITIONAL_TIMER_FREQUENCIES}} != 1  Additional timer frequency benchmarks disabled
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  10000000   10000   10  5

Benchmark Periodic Timeouts 10x 1000@1MHz
    Skip If  ${%{BENCH_ADDITIONAL_TIMER_FREQUENCIES}} != 1  Additional timer frequency benchmarks disabled
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  1000000    1000    10  5

Benchmark Periodic Timeouts 10x 100@100kHz
    Skip If  ${%{BENCH_ADDITIONAL_TIMER_FREQUENCIES}} != 1  Additional timer frequency benchmarks disabled
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  100000     100     10  5

Benchmark Periodic Timeouts 10x 10@10kHz
    Skip If  ${%{BENCH_ADDITIONAL_TIMER_FREQUENCIES}} != 1  Additional timer frequency benchmarks disabled
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  10000      10      10  5

####################
## 10 ms Timeouts ##
####################

Benchmark Periodic Timeouts 10x 100000@10MHz
    Skip If  ${%{BENCH_ADDITIONAL_TIMER_FREQUENCIES}} != 1  Additional timer frequency benchmarks disabled
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  10000000   100000  10  5

Benchmark Periodic Timeouts 10x 10000@1MHz
    Skip If  ${%{BENCH_ADDITIONAL_TIMER_FREQUENCIES}} != 1  Additional timer frequency benchmarks disabled
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  1000000    10000   10  5

Benchmark Periodic Timeouts 10x 1000@100kHz
    Skip If  ${%{BENCH_ADDITIONAL_TIMER_FREQUENCIES}} != 1  Additional timer frequency benchmarks disabled
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  100000     1000    10  5

Benchmark Periodic Timeouts 10x 100@10kHz
    Skip If  ${%{BENCH_ADDITIONAL_TIMER_FREQUENCIES}} != 1  Additional timer frequency benchmarks disabled
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  10000      100     10  5

#####################
## 100 ms Timeouts ##
#####################

Benchmark Periodic Timeouts 10x 1000000@10MHz
    Skip If  ${%{BENCH_ADDITIONAL_TIMER_FREQUENCIES}} != 1  Additional timer frequency benchmarks disabled
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  10000000   1000000     10  5

Benchmark Periodic Timeouts 10x 100000@1MHz
    Skip If  ${%{BENCH_ADDITIONAL_TIMER_FREQUENCIES}} != 1  Additional timer frequency benchmarks disabled
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  1000000    100000      10  5

Benchmark Periodic Timeouts 10x 10000@100kHz
    Skip If  ${%{BENCH_ADDITIONAL_TIMER_FREQUENCIES}} != 1  Additional timer frequency benchmarks disabled
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  100000     10000       10  5

Benchmark Periodic Timeouts 10x 1000@10kHz
    Skip If  ${%{BENCH_ADDITIONAL_TIMER_FREQUENCIES}} != 1  Additional timer frequency benchmarks disabled
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  10000      1000        10  5

##################
## 1 s Timeouts ##
##################

Benchmark Periodic Timeouts 10x 10000000@10MHz
    Skip If  ${%{BENCH_ADDITIONAL_TIMER_FREQUENCIES}} != 1  Additional timer frequency benchmarks disabled
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  10000000   10000000    10  5

Benchmark Periodic Timeouts 10x 1000000@1MHz
    Skip If  ${%{BENCH_ADDITIONAL_TIMER_FREQUENCIES}} != 1  Additional timer frequency benchmarks disabled
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  1000000    1000000     10  5

Benchmark Periodic Timeouts 10x 100000@100kHz
    Skip If  ${%{BENCH_ADDITIONAL_TIMER_FREQUENCIES}} != 1  Additional timer frequency benchmarks disabled
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  100000     100000      10  5

Benchmark Periodic Timeouts 10x 10000@10kHz
    Skip If  ${%{BENCH_ADDITIONAL_TIMER_FREQUENCIES}} != 1  Additional timer frequency benchmarks disabled
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Periodic Timeouts  10000      10000       10  5
