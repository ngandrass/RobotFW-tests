*** Settings ***
Documentation       Benchmark timer base operations.

# reset application and check DUT has correct firmware, skip all tests on error
Suite Setup         Run Keywords    PHILIP Reset
...                                 RIOT Reset
...                                 API Firmware Data Should Match
# reset application before running any test
Test Setup          Run Keywords    PHILIP Reset
...                                 RIOT Reset
...                                 API Sync Shell

# import libs and keywords
Resource            api_shell.keywords.txt
Resource            periph_utimer_benchmarks.keywords.txt

# add default tags to all tests
Force Tags          periph_utimer_benchmarks

*** Test Cases ***
Benchmark Timer Read
    [Teardown]                  Test Teardown

    API Call Should Succeed     Bench Timer Read
    API Call Should Succeed     PHILIP.Read Trace
    ${BENCH_TIMER_READ} =       Process Bench Timer Read    ${RESULT['data']}
    Record Property             bench_timer_read            ${BENCH_TIMER_READ}
