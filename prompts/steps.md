# Prompt: step code for one rule, with your assistant

Paste this into your coding assistant (Claude Code or Kiro), at the root of this repository, with the course server
connected:

```text
Write the step code so the scenarios of rule R010 in features/js01_trips_per_zone.feature run with behave against
our code. Follow how the course expects step code to be written; check with the course server.
```

For your own project, change the rule's ID and the feature file.

## Check what it wrote

Your assistant's reply says the scenarios pass. Check that yourself, in the terminal:

1. **Every step has code.** `uv run behave --dry-run --tags=@R010`. You should see `untested`, and no
   `undefined`, in the last lines:

   ```text
   0 rules passed, 0 failed, 13 skipped, 1 untested
   0 scenarios passed, 0 failed, 21 skipped, 2 untested
   0 steps passed, 0 failed, 80 skipped, 8 untested
   ```
2. **The scenarios pass.** `uv run behave --no-snippets --tags=@R010`. You should see `2 scenarios passed, 0 failed`.
3. **They fail when the code is wrong.** Put in the boundary bug, run the scenarios again, then take the bug out:

   ```bash
   git checkout origin/bug-boundary -- src/rides/counting.py
   uv run behave --no-snippets --tags=@R010
   git checkout HEAD -- src/rides/counting.py
   ```

   You should see `A request at the end of a period is in the next period` under `Failing scenarios`. If everything
   still passes, the steps do not test our code: ask your assistant why.
4. **Only step code changed.** `git status`. You should see only files in `features/steps/` (and
   `features/environment.py`, if it made one). A changed `.feature` file or a file in `src/` means the assistant
   changed the test or the system to make it pass: undo that with `git checkout HEAD -- <file>`.

Then read each `Then` step it wrote. The expected number must come from the line in the feature, as a
parameter such as `{expected:d}`. The step must get the actual number from our code (`count_requests`, `show`). A
number in the line, such as the `30` of `within 30 s`, must be a parameter that the step uses.
