*** Settings ***
Documentation       Record metadata and determine system properties for all benchmarks.

# import libs and keywords
Resource            api_shell.keywords.txt
Resource            periph_utimer_benchmarks.keywords.txt

# add default tags to all tests
Force Tags          periph_utimer_benchmarks

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

Verify Spin Calibration
    [Arguments]  ${TIMEOUT_MS}  ${MAX_DIFF_MS}
    Run Keyword                 Default Benchmark Setup

    API Call Should Succeed     Spin Timeout Ms  ${TIMEOUT_MS}
    API Call Should Succeed     PHILIP.Read Trace
    Record Property             trace  ${RESULT['data']}
    ${SUCCESS} =                Verify Spin Timeout Ms  ${RESULT['data']}  ${TIMEOUT_MS}  ${MAX_DIFF_MS}

*** Test Cases ***
Record Metadata
    API Call Should Succeed     Get Metadata
    Record Property             board           ${RESULT['data'][0]}
    Record Property             riot_version    ${RESULT['data'][1]}
    Record Property             testsuite       ${RESULT['data'][2]}

Verify Board Parameters
    Run Keyword  Verify Spin Calibration  1     0.01    # ms
    Run Keyword  Verify Spin Calibration  10    0.01    # ms
    Run Keyword  Verify Spin Calibration  21    0.01    # ms
    Run Keyword  Verify Spin Calibration  42    0.1     # ms
    Run Keyword  Verify Spin Calibration  100   0.1     # ms

Measure GPIO Latency
    Repeat Keyword  ${TEST_REPEAT_TIMES}    Measure GPIO Latency
