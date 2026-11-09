# Vale style sources

The repository uses Vale's built-in spelling and repetition checks, project
terminology rules, Microsoft spacing, and the write-good weasel-word warning.
The write-good warning applies only to `docs/`; backlog Markdown is checked
with the smaller global rule set. Warnings are advisory; errors fail the task.
This deliberately scoped policy avoids rewriting historical backlog records or
forcing editorial preferences such as contractions throughout technical text.

These selected upstream rules are checked in, with their MIT licenses, so normal
checks do not need a style download or `vale sync`:

- Microsoft 0.15.1, commit `59e9f790cc46000b35f1688b745147cface237fc`:
  `Microsoft/Spacing.yml`.
- write-good 0.4.1, commit `90c06e68dc5b6dddbc06c5961d94ba56a96b60d4`:
  `write-good/Weasel.yml`.

To update a rule, review the upstream release, replace the selected file and
license if needed, record its version and commit here, and rerun the prose and
script tests. Do not run `vale sync` over these vendored directories: it can
replace their contents. Add legitimate terms to the project vocabulary; its
entries are Vale regular expressions, so escape literal regex characters.
