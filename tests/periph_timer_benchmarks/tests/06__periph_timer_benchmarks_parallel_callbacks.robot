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
Benchmark Parallel Callbacks 1x 1ms@TIMER_SPEED
    FOR  ${n}  IN RANGE  ${TEST_REPEAT_TIMES}
        FOR  ${timeout_retries}  IN RANGE  5
            ${status}  ${value}=  Run Keyword And Ignore Error  Benchmark Parallel Callbacks  %{TIMER_SPEED}  %{TICKS_TIMER_SPEED_1ms}  1  50
            Run Keyword If  "${status}" == "PASS"  Exit For Loop  ELSE Log To Console  ${value}
        END
    END

Benchmark Parallel Callbacks 2x 1ms@TIMER_SPEED
    FOR  ${n}  IN RANGE  ${TEST_REPEAT_TIMES}
        FOR  ${timeout_retries}  IN RANGE  5
            ${status}  ${value}=  Run Keyword And Ignore Error  Benchmark Parallel Callbacks  %{TIMER_SPEED}  %{TICKS_TIMER_SPEED_1ms}  2  50
            Run Keyword If  "${status}" == "PASS"  Exit For Loop  ELSE Log To Console  ${value}
        END
    END

Benchmark Parallel Callbacks 3x 1ms@TIMER_SPEED
    FOR  ${n}  IN RANGE  ${TEST_REPEAT_TIMES}
        FOR  ${timeout_retries}  IN RANGE  5
            ${status}  ${value}=  Run Keyword And Ignore Error  Benchmark Parallel Callbacks  %{TIMER_SPEED}  %{TICKS_TIMER_SPEED_1ms}  3  50
            Run Keyword If  "${status}" == "PASS"  Exit For Loop  ELSE Log To Console  ${value}
        END
    END

Benchmark Parallel Callbacks 4x 1ms@TIMER_SPEED
    FOR  ${n}  IN RANGE  ${TEST_REPEAT_TIMES}
        FOR  ${timeout_retries}  IN RANGE  5
            ${status}  ${value}=  Run Keyword And Ignore Error  Benchmark Parallel Callbacks  %{TIMER_SPEED}  %{TICKS_TIMER_SPEED_1ms}  4  50
            Run Keyword If  "${status}" == "PASS"  Exit For Loop  ELSE Log To Console  ${value}
        END
    END

Benchmark Parallel Callbacks 5x 1ms@TIMER_SPEED
    FOR  ${n}  IN RANGE  ${TEST_REPEAT_TIMES}
        FOR  ${timeout_retries}  IN RANGE  5
            ${status}  ${value}=  Run Keyword And Ignore Error  Benchmark Parallel Callbacks  %{TIMER_SPEED}  %{TICKS_TIMER_SPEED_1ms}  5  50
            Run Keyword If  "${status}" == "PASS"  Exit For Loop  ELSE Log To Console  ${value}
        END
    END

Benchmark Parallel Callbacks 6x 1ms@TIMER_SPEED
    FOR  ${n}  IN RANGE  ${TEST_REPEAT_TIMES}
        FOR  ${timeout_retries}  IN RANGE  5
            ${status}  ${value}=  Run Keyword And Ignore Error  Benchmark Parallel Callbacks  %{TIMER_SPEED}  %{TICKS_TIMER_SPEED_1ms}  6  50
            Run Keyword If  "${status}" == "PASS"  Exit For Loop  ELSE Log To Console  ${value}
        END
    END

Benchmark Parallel Callbacks 7x 1ms@TIMER_SPEED
    FOR  ${n}  IN RANGE  ${TEST_REPEAT_TIMES}
        FOR  ${timeout_retries}  IN RANGE  5
            ${status}  ${value}=  Run Keyword And Ignore Error  Benchmark Parallel Callbacks  %{TIMER_SPEED}  %{TICKS_TIMER_SPEED_1ms}  7  50
            Run Keyword If  "${status}" == "PASS"  Exit For Loop  ELSE Log To Console  ${value}
        END
    END

Benchmark Parallel Callbacks 8x 1ms@TIMER_SPEED
    FOR  ${n}  IN RANGE  ${TEST_REPEAT_TIMES}
        FOR  ${timeout_retries}  IN RANGE  5
            ${status}  ${value}=  Run Keyword And Ignore Error  Benchmark Parallel Callbacks  %{TIMER_SPEED}  %{TICKS_TIMER_SPEED_1ms}  8  50
            Run Keyword If  "${status}" == "PASS"  Exit For Loop  ELSE Log To Console  ${value}
        END
    END
