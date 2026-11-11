Feature: Maturing heuristics and documentation rules
  Consumers can enable Strict maturing heuristic indicators and the CC9xx
  documentation and comment hygiene rules through pyproject.toml.

  Scenario: Consumer enables maturing Strict heuristics with absent-base silence
    Given a temporary project configured with maturing Strict heuristics
    And a Python module combining heuristic smells and an external subclass
    When Rude checks the maturing module
    Then maturing heuristic diagnostics emit INFO indicator messages
    And absent external base rules emit no false override or segregation claims

  Scenario: Consumer enables documentation and comment hygiene rules
    Given a temporary project configured with CC9xx documentation and comment rules
    And source and test modules exercising docstring drift, suppressions, and TODOs
    When Rude checks the documentation workspace
    Then CC9xx diagnostics report documentation and comment hygiene issues with expected severities
    And test files remain exempt from public docstring and marker requirements
