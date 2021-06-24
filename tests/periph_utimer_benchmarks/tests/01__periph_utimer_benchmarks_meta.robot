*** Settings ***
Documentation       Verify basic functionality of the Periph Timer API.

# reset application and check DUT has correct firmware, skip all tests on error
Suite Setup         Run Keywords    PHILIP Reset
...                                 RIOT Reset
...                                 API Firmware Should Match
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
    [Documentation]             Records metadata of this test run
    API Call Should Succeed     Get Metadata
    Record Property             board       ${RESULT['data'][0]}
    Record Property             testsuite   ${RESULT['data'][1]}
