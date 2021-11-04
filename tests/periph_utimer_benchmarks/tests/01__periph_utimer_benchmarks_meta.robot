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
Verify Spin Calibration
    [Arguments]  ${TIMEOUT_MS}  ${MAX_DIFF_MS}
    Run Keyword                 Default Benchmark Setup

    API Call Should Succeed     Spin Timeout Ms  ${TIMEOUT_MS}
    API Call Should Succeed     PHILIP.Read Trace
    Record Property             trace  ${RESULT['data']}
    ${SUCCESS} =                Verify Spin Timeout Ms  ${RESULT['data']}  ${TIMEOUT_MS}  ${MAX_DIFF_MS}  # False  # If false, test suite execution is not aborted upon error

*** Test Cases ***
Record Metadata
    API Call Should Succeed     Get Metadata
    Record Property             board                   ${RESULT['data'][0]}
    Record Property             riot_version            ${RESULT['data'][1]}
    Record Property             build_timestamp         ${RESULT['data'][2]}
    Record Property             testsuite               ${RESULT['data'][3]}
    Record Property             freq_cpu                ${RESULT['data'][4]}
    Record Property             instructions_per_spin   ${RESULT['data'][5]}
    Record Property             philip_backoff_spins    ${RESULT['data'][6]}
    Record Property             timer_speed             ${RESULT['data'][7]}

Verify Board Parameters
    ${fac}=      Convert To Number  ${%{SPIN_TIMEOUT_ACCEPTANCE_FACTOR}}
    Run Keyword  Verify Spin Calibration  1     ${{ 0.1 * ${fac} }}  # ms
    Run Keyword  Verify Spin Calibration  10    ${{ 0.1 * ${fac} }}  # ms
    Run Keyword  Verify Spin Calibration  21    ${{ 0.1 * ${fac} }}  # ms
    Run Keyword  Verify Spin Calibration  42    ${{ 0.1 * ${fac} }}  # ms
    Run Keyword  Verify Spin Calibration  100   ${{ 0.1 * ${fac} }}  # ms
    Run Keyword  Verify Spin Calibration  1000  ${{ 1.0 * ${fac} }}  # ms
