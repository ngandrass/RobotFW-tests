*** Settings ***
Documentation       Record metadata and determine system properties for all benchmarks.

# import libs and keywords
Resource            api_shell.keywords.txt
Resource            periph_timer_benchmarks.keywords.txt

# add default tags to all tests
Force Tags          periph_timer_benchmarks

Suite Setup         Run Keywords    Default Suite Setup
Test Setup          Run Keywords    Default Test Setup
Test Teardown       Run Keywords    Default Test Teardown

*** Keywords ***
Measure GPIO Latency
    Run Keyword                 Default Benchmark Setup

    API Call Should Succeed     Bench GPIO Latency
    API Call Should Succeed     PHILIP.Read Trace
#    Record Property             raw_trace                   ${RESULT['data']}
    ${BENCH_GPIO_LATENCY} =     Process Bench GPIO Latency  ${RESULT['data']}
    Record Property             bench_gpio_latency          ${BENCH_GPIO_LATENCY}

*** Test Cases ***
Record Metadata
    API Call Should Succeed     Get Metadata
    Record Property             board           ${RESULT['data'][0]}
    Record Property             riot_version    ${RESULT['data'][1]}
    Record Property             testsuite       ${RESULT['data'][2]}

Measure GPIO Latency
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Measure GPIO Latency
