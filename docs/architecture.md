# Architecture

## Boundaries

- `tui.py` and `cli.py` use only the public `ApplicationService` facade for application
  state and behavior. They retain the credential, LeetCode HTTP, and Solver process
  adapters required at the system boundary and contain no scheduling or persistence policy.
- `services.py` owns application queries, command orchestration, question-reference
  resolution, expected operational errors, refresh behavior, and Daily Plan policy.
- `fsrs_engine.py` is the only adapter to `py-fsrs`.
- `event_store.py` owns append-only, replication-safe facts.
- `projection.py` owns the disposable local SQLite read model and LeetCode metadata cache.
- `leetcode_client.py`, `credentials.py`, and `solver.py` are external adapters.

## Write and read paths

```text
TUI / CLI / application behavior tests -> ApplicationService -> append NDJSON Study Event
                                                           -> rescan Study Library files
                                                           -> rebuild local SQLite Projection

TUI / CLI <- immutable read values <- ApplicationService <- SQLite Projection
                                      |
                                      +-> replay reviews through py-fsrs
```

The event log is authoritative. SQLite uses WAL locally but is never replicated. Rebuilding after every current write favors correctness and a small interface over premature incremental-projection complexity.

`ApplicationService` exposes purpose-specific queries for the Daily Plan, Question
Cache search and lookup, library health, settings, and Solver input, plus direct intent
methods for writes. Its Projection, local configuration, Event Store, paths, access
flags, and diagnostic collections are private. Adapters receive frozen dataclasses,
enums, domain values, and tuples rather than SQLite rows or mutable storage objects.

Question Cache search reads only local SQLite metadata. Startup performs a best-effort
Study Library refresh, explicit refresh rescans and rebuilds, and each successful Study
Event write refreshes before returning so subsequent application reads see the change.

## Scheduling invariants

- Four ratings map directly to FSRS values 1 through 4.
- An Accepted import enrolls a new card but records no review.
- Suspended cards stay in history but are excluded from Today.
- Reviews due now or earlier come first; new cards fill remaining capacity.
- Defaults are a total limit of 20 and a new-card limit of 5.
- FSRS fuzzing is disabled so identical events and preferences produce identical projections.

## Local versus portable state

Portable events include account binding, enrollment, reviews, suspension, corrections, and scheduling preferences. The device ID, shared-directory location, solver command, credentials, question cache, and SQLite projection remain local.
