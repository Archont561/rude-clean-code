Feature: Package validation and release distribution builds

  Scenario: Validate local distributions with clean environment and wheel inspection
    Given a temporary project workspace with stale distribution artifacts and leaked PYTHONPATH
    When check_packages runs against a valid distribution build
    Then stale distribution artifacts are removed
    And build and twine check run without PYTHONPATH
    And twine validates both the sdist and wheel

  Scenario Outline: Reject incomplete or malformed local distribution artifacts
    Given a temporary project workspace for validation
    When check_packages inspects a wheel preset "<preset>" with sdist "<sdist_present>"
    Then package validation fails with "<error>"

    Examples:
      | preset           | sdist_present | error                            |
      | initializer_only | missing       | Expected one wheel and one sdist |
      | initializer_only | present       | License missing                  |
      | license_only     | present       | Package initializer missing      |

  Scenario: Reject a release build when the git tag mismatches pyproject version
    Given a temporary project workspace with version "0.1.0"
    When build_release runs for tag "v0.2.0"
    Then the release build fails with "does not match package version" before running subprocesses

  Scenario: Build and verify release distributions for a matching git tag
    Given a temporary project workspace with version "0.1.0", stale dist files, and leaked PYTHONPATH
    When build_release runs for tag "v0.1.0"
    Then stale dist files are removed
    And build and twine check run without PYTHONPATH for release artifacts

  Scenario: Dry-run a release build without a git tag
    Given a temporary project workspace with version "0.1.0"
    When build_release runs without a tag
    Then build and twine check run without PYTHONPATH for release artifacts

  Scenario: Reject a release build when dist contains an unexpected artifact count
    Given a temporary project workspace with version "0.1.0"
    When build_release produces only a wheel without an sdist
    Then the release build fails with "Expected one wheel and one sdist"
