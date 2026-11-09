# Documentation standard

This is the canonical standard for documentation in this repository. It
defines what the `docs/` directory is for, what good documentation looks
like, how documentation is validated, and what "done" means for a change that
affects documentation. A change is not fully documented simply because its
implementation is complete.

## Purpose

The `docs/` directory is the primary user-facing knowledge layer of this
repository.

It contains the maintained, discoverable source of truth for understanding,
using, configuring, and operating the software.

Documentation should serve both human users and AI agents. It must be
accurate, actionable, easy to navigate, and consistent with the actual
implementation.

## Principles

1. **Documentation is part of the product.** It is not an afterthought or an
   optional summary of implementation.
2. **Prefer one canonical explanation.** Avoid duplicating the same
   knowledge across multiple documents.
3. **Document observable behavior.** Describe what the software actually
   does, not merely what was intended.
4. **Write for users first.** Prefer practical explanations, examples, and
   clear instructions over implementation-centric descriptions.
5. **Keep documentation discoverable.** Organize documents by purpose and
   provide clear navigation.
6. **Treat outdated documentation as a defect.** Incorrect instructions and
   obsolete references must be corrected.

## Suggested structure

- `guides/` — task-oriented instructions and workflows.
- `concepts/` — domain concepts and explanations.
- `reference/` — APIs, configuration, commands, and schemas.
- `architecture/` — system architecture and architectural decisions.
- `development/` — contribution, testing, and development workflows.

The root `README.md` should provide an introduction and direct users to the
relevant documentation.

## Preventing documentation drift

Documentation must evolve alongside the software.

Every change that affects user-visible behavior, configuration, APIs,
workflows, or operational requirements must include an assessment of its
documentation impact.

During implementation and review:

- Identify affected documentation.
- Update existing canonical documents instead of creating unnecessary
  duplicates.
- Add documentation when introducing new user-facing capabilities.
- Remove obsolete instructions, examples, and references.
- Verify that commands, configuration examples, and code snippets remain
  valid.
- Ensure internal links and navigation resolve correctly.

A change is not considered fully documented simply because its implementation
is complete.

## Validation

Documentation quality is maintained through automated checks and human
review.

Recommended validation layers:

- **alint:** repository conventions and structural rules.
- **markdownlint-cli2:** markdown formatting and consistency.
- **Vale:** writing style, terminology, and language quality.
- **lychee:** broken links and references.

Run documentation checks in CI and require them to pass before merging.

Automated checks are necessary but insufficient. Reviewers must also assess
whether documentation accurately reflects the implemented behavior.

### How these layers are wired in this repository

- `alint` (`.alint.yml`, run by `pixi run --locked doit alint` in the CI
  `Policy` job) requires the structure and entry points of this documentation
  tree.
- `markdownlint-cli2` (config `.markdownlint-cli2.jsonc`, run by
  `pixi run --locked doit docs-lint` and the CI `Documentation` job) checks
  formatting and consistency of the maintained markdown surface.
- `Vale` (`.vale.ini`, run by `pixi run --locked doit lint-prose` in the CI
  `Policy` job) checks style, terminology, and language quality; project
  terminology lives in `.vale/styles/config/vocabularies/Project/accept.txt`
  and substitution rules in `.vale/styles/Project/Terms.yml`.
- `lychee` (CI `Documentation` job) checks that links and references resolve.

Vendored (`.agents/`) and immutable backlog (`backlog/`) markdown are
intentionally excluded from markdownlint and lychee; backlog files are edited
through the `backlog` tooling, and vendored skills are owned upstream.

## Definition of done

A change affecting documentation must satisfy the following:

- Relevant documentation has been identified.
- Existing documentation has been updated where necessary.
- New user-facing behavior is documented.
- Examples and instructions reflect the current implementation.
- Obsolete information has been removed.
- Documentation validation passes.

If no documentation change is necessary, that decision should be explicit
during review.

## Ownership

Every contributor changing the product is responsible for assessing its
documentation impact.

Documentation is maintained continuously as part of normal development, not
deferred to occasional cleanup exercises.

The goal is for `docs/` to remain a trustworthy representation of the
software at all times.
