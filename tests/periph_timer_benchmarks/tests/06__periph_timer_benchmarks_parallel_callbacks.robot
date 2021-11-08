*** Settings ***
Documentation       Benchmark callback execution of simultaneously ellapsing timeouts.

# import libs and keywords
Resource            api_shell.keywords.txt
Resource            periph_timer_benchmarks.keywords.txt

# add default tags to all tests
Force Tags          periph_timer_benchmarks

Suite Setup         Run Keywords    Default Suite Setup
Test Setup          Run Keywords    Default Test Setup
Test Teardown       Run Keywords    Default Test Teardown

*** Keywords ***
Benchmark Parallel Callbacks
    [Arguments]  ${FREQ}  ${TICKS}  ${CHANNELS}  ${REPEATS}
    Run Keyword                 Default Benchmark Setup

    # Check arguments
    Should be True  ${REPEATS} <= 50  # Don't generate more events than PHiLIP trace can hold

    # Execute
    FOR  ${n}  IN RANGE  ${REPEATS}
        API Call Should Succeed Or Skip  Bench Parallel Callbacks  ${FREQ}  ${TICKS}  ${CHANNELS}
    END

    # Evaluate
    API Call Should Succeed     PHILIP.Read Trace
    Record Property             trace  ${RESULT['data']}

    ${BENCH_RESULT} =           Process Bench Parallel Callbacks  ${RESULT['data']}
    Record Property             frequency                         ${FREQ}
    Record Property             ticks                             ${TICKS}
    Record Property             channels                          ${CHANNELS}
    Record Property             repeats                           ${REPEATS}
    Record Property             bench_parallel_callbacks          ${BENCH_RESULT}

*** Test Cases ***
Benchmark Parallel Callbacks 1x 1000@TIMER_SPEED
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Parallel Callbacks  ${%{TIMER_SPEED}}  1000  1  50

Benchmark Parallel Callbacks 2x 1000@TIMER_SPEED
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Parallel Callbacks  ${%{TIMER_SPEED}}  1000  2  50

Benchmark Parallel Callbacks 3x 1000@TIMER_SPEED
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Parallel Callbacks  ${%{TIMER_SPEED}}  1000  3  50

Benchmark Parallel Callbacks 4x 1000@TIMER_SPEED
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Parallel Callbacks  ${%{TIMER_SPEED}}  1000  4  50

Benchmark Parallel Callbacks 5x 1000@TIMER_SPEED
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Parallel Callbacks  ${%{TIMER_SPEED}}  1000  5  50

Benchmark Parallel Callbacks 6x 1000@TIMER_SPEED
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Parallel Callbacks  ${%{TIMER_SPEED}}  1000  6  50

Benchmark Parallel Callbacks 7x 1000@TIMER_SPEED
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Parallel Callbacks  ${%{TIMER_SPEED}}  1000  7  50

Benchmark Parallel Callbacks 8x 1000@TIMER_SPEED
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Parallel Callbacks  ${%{TIMER_SPEED}}  1000  8  50
