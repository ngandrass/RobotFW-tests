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

*** Test Cases ***
Benchmark uAPI Timer Read
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark uAPI Timer Read

Benchmark hAPI Timer Read
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark hAPI Timer Read

Benchmark uAPI Timer Write
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark uAPI Timer Write

Benchmark hAPI Timer Write
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Benchmark hAPI Timer Write
