Feature: Module and package organization Clean Code rules
  Scenario: Oversized module receives a tailored non-autofix split suggestion
    Given a temporary module project with CC001 max_lines set to 12
    And a Python module with two separate symbol clusters exceeding 12 lines
    When Rude runs CC0 checks on the module project
    Then Rude reports CC001 without an autofix and suggests splitting by clusters

  Scenario: Package initializer permits facade constructs and configured VERSION
    Given a temporary module project checking CC002 with VERSION allowed
    And a package initializer with VERSION, TYPE_CHECKING, __all__, and a helper function
    When Rude runs CC0 checks on the module project
    Then Rude flags only the helper function in __init__.py at INFO severity

  Scenario: Non-empty initializer requires __all__ while marker files stay silent
    Given a temporary module project checking CC003
    And an empty marker __init__.py alongside a non-empty __init__.py missing __all__
    When Rude runs CC0 checks on the module project
    Then Rude flags only the non-empty __init__.py for missing __all__

  Scenario: Deep relative imports and private __all__ exports are flagged
    Given a temporary module project checking CC004 and CC005
    And a module with a 3-dot relative import and __all__ containing a private name and a dunder
    When Rude runs CC0 checks on the module project
    Then Rude reports CC004 and CC005 while keeping __version__ exempt
