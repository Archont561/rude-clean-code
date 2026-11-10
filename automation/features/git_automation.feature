Feature: Git hook installation and commit message validation

  Scenario: Verify already installed Lefthook hooks without reinstalling
    Given Lefthook hooks are already installed
    When install_hooks runs
    Then only hook status verification runs and reports "already installed"

  Scenario: Install Lefthook hooks when missing and verify installation
    Given Lefthook hooks are not yet installed
    When install_hooks runs
    Then Lefthook installs hooks, re-verifies status, and reports "hooks installed"

  Scenario: Fail loudly when Lefthook hook check returns an unexpected error
    Given Lefthook hook verification exits with status 2
    When install_hooks runs
    Then hook installation fails with "exit 2"

  Scenario Outline: Skip commit message validation when head or resolved base is invalid
    Given a git repository with commits "abc123", "def456", and "HEAD^"
    When commit messages are checked for base "<base>" and head "<head>"
    Then commit message validation skips with message "<output>"

    Examples:
      | base   | head   | output                      |
      |        |        | skipping commit-message check |
      | badref | def456 | No valid base ref available |

  Scenario: Derive base commit from HEAD parent when base is the zero SHA
    Given a git repository with commits "abc123", "def456", and "HEAD^" where HEAD parent is "abc123"
    When commit messages are checked for the zero SHA base and head "def456"
    Then convco checks commit range "abc123..def456"

  Scenario: Fall back to repository root commit when HEAD has no parent
    Given a git repository without HEAD parent and root commit "rootsha" with head "def456"
    When commit messages are checked for base "" and head "def456"
    Then convco checks commit range "rootsha..def456"
