# ADR 002: Replicated event library and local projection

Status: accepted

## Context

Synchronizing one mutable SQLite or JSON file through file replication services creates conflicts and makes recovery ambiguous. Implementing a custom network synchronization service is out of scope.

## Decision

The shared Study Library contains immutable NDJSON events partitioned by device UUID and UTC day. A device-local SQLite Projection is rebuilt from those events and is never synchronized. Syncthing, a mounted WebDAV client, or an equivalent tool transports the shared files.

Credentials, device UUID, solver command, question metadata cache, and SQLite files remain local. Corrupt complete records are reported and skipped; an incomplete last record is ignored until complete. No pre-2.0 JSON migration is provided.

## Consequences

Normal devices never append to the same file. The number of files grows per active device-day rather than per review. Query speed does not compromise recoverability because SQLite is disposable.
