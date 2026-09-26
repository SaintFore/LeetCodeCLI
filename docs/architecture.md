# Architecture

## Boundaries

- `tui.py` and `cli.py` are adapters. They contain no scheduling or persistence policy.
- `services.py` owns use cases and daily-plan policy.
- `fsrs_engine.py` is the only adapter to `py-fsrs`.
- `event_store.py` owns append-only, replication-safe facts.
- `projection.py` owns the disposable local SQLite read model and LeetCode metadata cache.
- `leetcode_client.py`, `credentials.py`, and `solver.py` are external adapters.

## Write and read paths

```text
TUI / CLI -> ApplicationService -> append NDJSON event
                                  -> rescan all event files
                                  -> rebuild local SQLite projection

TUI / CLI <- daily plan <- replay reviews through py-fsrs <- SQLite projection
```

The event log is authoritative. SQLite uses WAL locally but is never replicated. Rebuilding after every current write favors correctness and a small interface over premature incremental-projection complexity.

## Scheduling invariants

- Four ratings map directly to FSRS values 1 through 4.
- An Accepted import enrolls a new card but records no review.
- Suspended cards stay in history but are excluded from Today.
- Reviews due now or earlier come first; new cards fill remaining capacity.
- Defaults are a total limit of 20 and a new-card limit of 5.
- FSRS fuzzing is disabled so identical events and preferences produce identical projections.

## Local versus portable state

Portable events include account binding, enrollment, reviews, suspension, corrections, and scheduling preferences. The device ID, shared-directory location, solver command, credentials, question cache, and SQLite projection remain local.
