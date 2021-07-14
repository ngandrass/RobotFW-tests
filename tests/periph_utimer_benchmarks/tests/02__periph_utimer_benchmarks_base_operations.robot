*** Settings ***
Documentation       Benchmark timer base operations.

# import libs and keywords
Resource            api_shell.keywords.txt
Resource            periph_utimer_benchmarks.keywords.txt

# add default tags to all tests
Force Tags          periph_utimer_benchmarks

Suite Setup         Run Keywords    Default Suite Setup
Test Setup          Run Keywords    Default Test Setup
Test Teardown       Run Keywords    Default Test Teardown

*** Keywords ***
Benchmark uAPI Timer Read
    Run Keyword                 Default Benchmark Setup

    API Call Should Succeed     Bench Timer Read            uAPI
    API Call Should Succeed     PHILIP.Read Trace
    Record Property             trace                       ${RESULT['data']}

    ${BENCH_TIMER_READ} =       Process Bench Timer Read    ${RESULT['data']}
    Record Property             bench_timer_read_uapi       ${BENCH_TIMER_READ}

Benchmark hAPI Timer Read
    Run Keyword                 Default Benchmark Setup

    API Call Should Succeed     Bench Timer Read            hAPI
    API Call Should Succeed     PHILIP.Read Trace
    Record Property             trace                       ${RESULT['data']}

    ${BENCH_TIMER_READ} =       Process Bench Timer Read    ${RESULT['data']}
    Record Property             bench_timer_read_hapi       ${BENCH_TIMER_READ}

Benchmark uAPI Timer Write
    Run Keyword                 Default Benchmark Setup

    API Call Should Succeed     Bench Timer Write           uAPI
    API Call Should Succeed     PHILIP.Read Trace
    Record Property             trace                       ${RESULT['data']}

    ${BENCH_TIMER_WRITE} =      Process Bench Timer Write   ${RESULT['data']}
    Record Property             bench_timer_write_uapi      ${BENCH_TIMER_WRITE}

Benchmark hAPI Timer Write
    Run Keyword                 Default Benchmark Setup

    API Call Should Succeed     Bench Timer Write           hAPI
    API Call Should Succeed     PHILIP.Read Trace
    Record Property             trace                       ${RESULT['data']}

    ${BENCH_TIMER_WRITE} =      Process Bench Timer Read    ${RESULT['data']}
    Record Property             bench_timer_write_hapi      ${BENCH_TIMER_WRITE}

Benchmark uAPI Timer Set
    Run Keyword                 Default Benchmark Setup

    API Call Should Succeed     Bench Timer Set             uAPI
    API Call Should Succeed     PHILIP.Read Trace
    Record Property             trace                       ${RESULT['data']}

    ${BENCH_TIMER_SET} =        Process Bench Timer Set     ${RESULT['data']}
    Record Property             bench_timer_set_uapi        ${BENCH_TIMER_SET}

Benchmark hAPI Timer Set
    Run Keyword                 Default Benchmark Setup

    API Call Should Succeed     Bench Timer Set             hAPI
    API Call Should Succeed     PHILIP.Read Trace
    Record Property             trace                       ${RESULT['data']}

    ${BENCH_TIMER_SET} =        Process Bench Timer Set     ${RESULT['data']}
    Record Property             bench_timer_set_hapi        ${BENCH_TIMER_SET}

Benchmark uAPI Timer Clear
    Run Keyword                 Default Benchmark Setup

    API Call Should Succeed     Bench Timer Clear           uAPI
    API Call Should Succeed     PHILIP.Read Trace
    Record Property             trace                       ${RESULT['data']}

    ${BENCH_TIMER_CLEAR} =      Process Bench Timer Clear   ${RESULT['data']}
    Record Property             bench_timer_clear_uapi      ${BENCH_TIMER_CLEAR}

Benchmark hAPI Timer Clear
    Run Keyword                 Default Benchmark Setup

    API Call Should Succeed     Bench Timer Clear           hAPI
    API Call Should Succeed     PHILIP.Read Trace
    Record Property             trace                       ${RESULT['data']}

    ${BENCH_TIMER_CLEAR} =      Process Bench Timer Clear   ${RESULT['data']}
    Record Property             bench_timer_clear_hapi      ${BENCH_TIMER_CLEAR}

*** Test Cases ***
Benchmark uAPI Timer Read
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark uAPI Timer Read

Benchmark hAPI Timer Read
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark hAPI Timer Read

Benchmark uAPI Timer Write
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark uAPI Timer Write

Benchmark hAPI Timer Write
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark hAPI Timer Write

Benchmark uAPI Timer Set
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark uAPI Timer Set

Benchmark hAPI Timer Set
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark hAPI Timer Set

Benchmark uAPI Timer Clear
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark uAPI Timer Clear

Benchmark hAPI Timer Clear
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark hAPI Timer Clear
