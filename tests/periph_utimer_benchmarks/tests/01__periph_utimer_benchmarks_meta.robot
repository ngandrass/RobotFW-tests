*** Settings ***
Documentation       Verify basic functionality of the Periph Timer API.

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
Record Metadata
    [Teardown]                  Test Teardown

    API Call Should Succeed     Get Metadata
    Record Property             board           ${RESULT['data'][0]}
    Record Property             riot_version    ${RESULT['data'][1]}
    Record Property             testsuite       ${RESULT['data'][2]}

Measure GPIO Latency
    [Teardown]                  Test Teardown

    # Only record rising edges
    Run Keyword                 PHILIP.Write and Execute  tmr.mode.trig_edge  1

    API Call Should Succeed     Bench GPIO Latency
    API Call Should Succeed     PHILIP.Read Trace
    Record Property             bench_gpio_latency  ${RESULT['data']}

    # ${GPIO_LATENCY}=           DutDeviceIf.Compress Result  ${RESULT['data']}
    # Record Property            gpio_latency                 ${GPIO_LATENCY['diff']}
