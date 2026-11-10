Feature: Unified repository task automation with doit

  Scenario: Discover the complete automation task catalogue
    Given the automation task module is loaded
    Then the default task is "ci" with backend "sqlite3"
    And all expected repository automation tasks are registered
    And "docs-lint" depends on "bun-install"
    And "dogfood" depends on "install-projects"
    And "lint" depends on "dogfood"
    And composite task groups only depend on registered tasks

  Scenario: Resolve repository root via doit configuration
    Given the repository doit configuration
    When doit configuration is inspected
    Then dodoFile targets "automation/dodo.py" from "."
    And the task module resolves ROOT to the repository root

  Scenario: Clean generated build and coverage artifacts
    Given a temporary workspace with generated coverage and distribution artifacts
    When the automation clean helpers run
    Then generated coverage and distribution artifacts are removed

  Scenario: Invoke doit CLI from the repository root without an explicit file flag
    When doit list runs from the repository root
    Then the listed tasks include "test-automation" and "ci"

  Scenario: Dogfood Rude checks pass when clean and fail on diagnostics
    Given a temporary workspace configured for Rude dogfooding
    When dogfood_rude runs with clean Rude output
    Then dogfood_rude succeeds and prints "0 diagnostics"
    When dogfood_rude runs and Rude emits a CC diagnostic
    Then dogfood_rude fails with "CC101"
