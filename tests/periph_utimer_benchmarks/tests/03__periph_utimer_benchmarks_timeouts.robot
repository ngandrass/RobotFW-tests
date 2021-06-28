*** Settings ***
Documentation       Benchmark timeout operations.

# import libs and keywords
Resource            api_shell.keywords.txt
Resource            periph_utimer_benchmarks.keywords.txt

# add default tags to all tests
Force Tags          periph_utimer_benchmarks

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
    ${BENCH_RESULT} =           Process Bench Absolute Timeout  ${RESULT['data']}
    Record Property             frequency                       ${FREQ}
    Record Property             ticks                           ${TICKS}
    Record Property             repeats                         ${REPEATS}
    Record Property             bench_absolute_timeouts         ${BENCH_RESULT}

*** Test Cases ***
Benchmark Absolute Timeouts 10000@10MHz 1ms
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  10000000   10000   50

Benchmark Absolute Timeouts 1000@1MHz 1ms
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  1000000    1000    50

Benchmark Absolute Timeouts 100@100kHz 1ms
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  100000     100     50

Benchmark Absolute Timeouts 10@10kHz 1ms
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Absolute Timeouts  10000      10      50
