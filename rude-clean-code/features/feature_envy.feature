Feature: Feature Envy and coupling refinements
  Consumers can enable the CC606 Feature Envy indicator for external helpers
  that compare two instances of a type they do not own, and escalate CC605 to
  selected dunders through pyproject.toml.

  Scenario: Consumer enables the CC606 indicator on an external same-type helper
    Given a temporary project configured with the CC606 Feature Envy indicator
    And a module whose helper compares two instances of an imported type
    And a module whose helpers compare builtin values or live on the type itself
    When Rude checks the Feature Envy workspace
    Then CC606 reports the external same-type pair with indicator wording
    And CC606 stays silent for builtin annotations and in-type comparison methods

  Scenario: Consumer escalates CC605 to selected dunders
    Given a temporary project configured with flagged CC605 dunders
    And a module reading escalated and non-escalated dunder members
    When Rude checks the dunder workspace
    Then CC605 reports only the escalated dunder members
    And CC605 keeps ordinary protocol dunders silent
