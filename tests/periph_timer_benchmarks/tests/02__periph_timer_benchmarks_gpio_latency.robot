*** Settings ***
Documentation       Measure GPIO latency.

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
    [Arguments]  ${TIMEOUT_US}
    Run Keyword                 Default Benchmark Setup

    API Call Should Succeed     Bench GPIO Latency          ${TIMEOUT_US}
    API Call Should Succeed     PHILIP.Read Trace
    Record Property             trace                       ${RESULT['data']}
    ${BENCH_GPIO_LATENCY} =     Process Bench GPIO Latency  ${RESULT['data']}  ${TIMEOUT_US}
    Record Property             bench_gpio_latency          ${BENCH_GPIO_LATENCY}
    Record Property             timeout_us                  ${TIMEOUT_US}

*** Test Cases ***
Measure GPIO Latency 1us
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Measure GPIO Latency  1     #us

Measure GPIO Latency 10us
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Measure GPIO Latency  10    #us

Measure GPIO Latency 100us
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Measure GPIO Latency  100   #us

Measure GPIO Latency 1000us
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Measure GPIO Latency  1000  #us
