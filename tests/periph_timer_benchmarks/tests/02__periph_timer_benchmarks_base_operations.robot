*** Settings ***
Documentation       Benchmark timer base operations.

# import libs and keywords
Resource            api_shell.keywords.txt
Resource            periph_timer_benchmarks.keywords.txt

# add default tags to all tests
Force Tags          periph_timer_benchmarks

Suite Setup         Run Keywords    Default Suite Setup
Test Setup          Run Keywords    Default Test Setup
Test Teardown       Run Keywords    Default Test Teardown

*** Keywords ***
Benchmark Timer Read
    Run Keyword                 Default Benchmark Setup

    API Call Should Succeed     Bench Timer Read
    API Call Should Succeed     PHILIP.Read Trace
    Record Property             trace                       ${RESULT['data']}

    ${BENCH_TIMER_READ} =       Process Bench Timer Read    ${RESULT['data']}
    Record Property             bench_timer_read            ${BENCH_TIMER_READ}

Benchmark Timer Set
    Run Keyword                 Default Benchmark Setup

    API Call Should Succeed     Bench Timer Set
    API Call Should Succeed     PHILIP.Read Trace
    Record Property             trace                       ${RESULT['data']}

    ${BENCH_TIMER_SET} =        Process Bench Timer Set     ${RESULT['data']}
    Record Property             bench_timer_set             ${BENCH_TIMER_SET}

Benchmark Timer Clear
    Run Keyword                 Default Benchmark Setup

    API Call Should Succeed     Bench Timer Clear
    API Call Should Succeed     PHILIP.Read Trace
    Record Property             trace                       ${RESULT['data']}

    ${BENCH_TIMER_CLEAR} =      Process Bench Timer Clear   ${RESULT['data']}
    Record Property             bench_timer_clear           ${BENCH_TIMER_CLEAR}

*** Test Cases ***
Benchmark Timer Read
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Timer Read

Benchmark Timer Set
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Timer Set

Benchmark Timer Clear
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark Timer Clear
