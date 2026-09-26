# Study data replication

LeetCode FSRS does not implement a network sync protocol. Point every device at a folder replicated by Syncthing, a mounted WebDAV client, or another tool that preserves ordinary files.

## Why one file per device per UTC day

Each device writes only below its own UUID directory, which avoids normal cross-device writes to the same file. Daily rotation limits the amount copied after an append while avoiding one-file-per-review growth. File count is bounded by active devices and active days.

Do not copy a local device configuration to another machine: it contains the writer UUID. If two machines share that UUID they can append to the same file and create avoidable conflicts.

## Safe setup

1. Let the external tool finish creating or downloading the shared folder.
2. Run `leetcode-fsrs init PATH --timezone IANA_ZONE` on each device.
3. Run `leetcode-fsrs status` after replication. The same account should be shown everywhere.
4. Run `leetcode-fsrs import-accepted` on each device that needs searchable question metadata; this cache is intentionally local.
5. Sync the entire shared folder. Do not sync XDG config, credentials, or `projection.sqlite3`.

`init` attaches to an existing `library.json`; it does not replace it. A library is bound to one `leetcode.com` username. A conflicting account event is reported rather than silently merging two people's histories.

## Failure behavior

- Missing or non-writable shared directory: reads continue from the last local projection where possible; new study writes are rejected.
- Incomplete final NDJSON line: ignored until a later scan sees its newline.
- Invalid complete line: reported with file and line, then skipped.
- Duplicate event ID with identical contents: deduplicated.
- Duplicate event ID with different contents: reported as corruption.

Before manually repairing a file, stop the app on all devices and make a backup of the shared directory. Immutable historical lines should ordinarily never be edited.
