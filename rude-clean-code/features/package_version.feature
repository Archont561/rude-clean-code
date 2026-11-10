Feature: Rude Clean Code package version discovery
  Scenario: Discover the installed Rude Clean Code package version
    Given the package is installed
    When its root namespace is inspected
    Then VERSION is its only public export
    And VERSION matches pyproject and installed distribution metadata
    And VERSION is read from distribution metadata
    And importing the root namespace does not load rude or plugin submodules
