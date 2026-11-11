Feature: Deterministic Clean Code core rules
  Scenario: Rude discovers Clean Code rules via entry point
    Given the rude-clean-code plugin is installed
    When Rude discovers plugin rules
    Then all registered CC rules are available with their documented severities
    And selecting by CC, family prefix, or exact code filters the matching rules

  Scenario: Consumer runs Basic profile and configured thresholds on Python code
    Given a temporary project configured with the Basic profile
    And a Python file violating deterministic CC rules and a clean nested function
    When Rude checks the temporary project
    Then diagnostics report measured value, configured limit, and suggested action as warnings
    And Rude exits successfully without treating warnings as errors

  Scenario: Consumer overrides a deterministic rule threshold in pyproject.toml
    Given a temporary project setting CC101 max_lines to 4
    And a Python function spanning 5 lines
    When Rude checks the temporary project
    Then Rude reports CC101 with measured 5 and limit 4

  Scenario: Dogfooding Clean Code rules on the package source
    Given the rude-clean-code plugin is installed
    When Rude checks the package source directory with the project Basic profile
    Then no CC diagnostics are emitted

  Scenario: Consumer runs Strict profile including in-file heuristics
    Given a temporary project configured with the Strict profile
    And a Python file violating heuristic CC rules
    When Rude checks the temporary project
    Then Strict heuristic diagnostics carry expected severities and same-file guidance
    And Rude exits successfully without treating warnings as errors
