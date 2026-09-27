---
name: log-ai-decision
description: Add an entry to docs/ai-development.md, the project's record of how AI-generated work was evaluated, changed or rejected. Use after a significant design decision, a rejected approach, or a bug that validation caught, or when asked to "log this" or "add it to the AI log".
---

# Log an AI-assisted decision

`docs/ai-development.md` is evaluated as evidence that AI was used as an
engineering assistant, not an unquestioned code generator. An entry is only
worth writing if something was **decided, rejected or caught**. Routine work
doesn't get an entry.

## Format

Number it after the last entry: a new top-level number, or a lettered
sub-entry when it continues an existing thread (like 9a–9e). Use these
headings, and leave out any that don't apply:

```markdown
## <n>. <Area>: <what happened, in plain words>

**Prompt/goal:** what was asked, quoted if short.

**Accepted:** what was built and why, specifically enough to find it in the code.

**Rejected:** alternatives that were considered, and why each lost.

**Found by <how>:** bugs or wrong assumptions that validation caught,
including your own mistakes. What the evidence was, and what fixed it.

**Validated:** the commands, tests or checks that were run and what they
returned (with numbers).
```

## Rules

- **Only record what happened.** Every number comes from a command that was
  actually run. If a check wasn't done, say so ("not tested because…").
- **Include your own mistakes.** Wrong assumptions, a first attempt that
  failed, a figure that was misreported. These are the most valuable entries.
- **Be specific.** Name files, functions, tests and values. "Improved error
  handling" says nothing; "caught `IntegrityError` before the retry branch"
  does.
- **Update, don't contradict.** If a later change supersedes an earlier entry,
  add a one-line *Later amended:* pointer to the old entry instead of leaving
  two entries that disagree.
- Plain sentences, no marketing tone. The reader is a senior engineer.
