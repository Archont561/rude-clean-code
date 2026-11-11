Feature: Config-driven architecture and design-pattern boundaries
  Consumers can opt into CC7xx architecture dependency rules and CC8xx pattern
  boundary rules by configuring their own modules, classes, and layer paths.

  Scenario: Unconfigured Architecture profile emits no diagnostics on a project tree
    Given a temporary configuration selecting the Architecture profile without rule options
    When Rude checks the consumer fixture tree
    Then no architecture or pattern diagnostics are reported

  Scenario: Configured Architecture profile flags violations only outside legitimate boundaries
    Given a temporary configuration declaring consumer modules, classes, and layer paths
    When Rude checks the consumer fixture tree
    Then configured CC7xx and CC8xx diagnostics flag violations with expected severities
    And legitimate repository, factory, strategy, handler, and composition files stay clean
