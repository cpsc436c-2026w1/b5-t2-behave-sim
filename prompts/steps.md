# Prompt: step code for one rule, with your assistant

Paste this into your coding assistant (Claude Code or Kiro), at the root of this repository. The connection to the
course server is optional: the same prompt works with it and without it.

```text
Write the step code so the scenarios of rule R010 in features/js01_trips_per_zone.feature run with behave against
our code. Follow how the step code already in features/steps/ is written; if you are connected to the course
server, also check what its pages say about step code.
This is B5T2 tutorial practice for Checkpoint 2, not the Checkpoint 1 hand-in. Do not commit: I check your changes
with git myself.
```

For your own project, change the rule's ID and the feature file.

## Check what it wrote

Your assistant's reply says the scenarios pass. Check that yourself, in the terminal, in this order. Check 1 comes
first: it reads what the assistant changed before any later check restores a file.

1. **Only step code changed.**

   ```bash
   git status --short
   ```

   You should see only files in `features/steps/` (and `features/environment.py`, already in this repository, if
   it changed it). A file in `src/` or a `.feature` file in the list means the assistant changed the system or the
   test to make it pass. Read what it changed, then undo it, one `git restore` for each file listed:

   ```bash
   git diff -- src/ 'features/*.feature'
   git diff --cached -- src/ 'features/*.feature'
   git restore --staged --worktree <file>
   ```

   A new file there (`??` in the list) is not undone by `git restore`: delete it.
2. **Every step has code.**

   ```bash
   uv run behave --dry-run --tags=@R010
   ```

   You should see `untested`, and no `undefined`, in the last lines.
3. **The scenarios pass.**

   ```bash
   uv run behave --no-snippets --tags=@R010
   ```

   You should see both R010 scenarios passed and `0 failed`.
4. **They fail when the code is wrong.** Put in the boundary bug, run the scenarios again, then take the bug out:

   ```bash
   git restore --source origin/bug-boundary -- src/rides/counting.py
   uv run behave --no-snippets --tags=@R010
   git restore src/rides/counting.py
   ```

   You should see `A request exactly at the end of a period (09:05:00)` under `Failing scenarios`. If everything
   still passes, the steps do not catch the boundary bug: ask your assistant why. After the last line,
   `git status --short` lists no file in `src/`.

Then read each `Then` step it wrote. The expected number must come from the line in the feature, as a
parameter such as `{expected:d}`. The step must get the actual number from our code (`count_requests`, `show`, or
`count_between`, which calls `show`). A number or time in the line, such as the `60` of `within 60 s` or the end of
a period, must be a parameter that the step uses.
