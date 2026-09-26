# LeetCode FSRS

This context defines the language for planning LeetCode practice with spaced repetition across terminal interfaces and multiple devices.

## Language

**LeetCode Import**:
The ingestion of problem metadata and submission history from a user's LeetCode account. It does not transfer application-owned learning history between devices.
_Avoid_: LeetCode Sync, Account Sync

**Study Data Replication**:
The propagation of application-owned learning data between devices by a user-selected external folder synchronization service. The application defines sync-safe artifacts and guidance but does not own accounts or network transport.
_Avoid_: Cloud Sync, LeetCode Import

**Study Library**:
One append-only event collection bound to one `leetcode.com` account and one fixed IANA timezone. A library may be replicated to multiple devices.
_Avoid_: Database, Profile

**Study Event**:
An immutable fact such as card enrollment, review rating, suspension, correction, or preference change. Events are the authoritative study history.
_Avoid_: Row, Sync Record

**Projection**:
A device-local, rebuildable SQLite read model derived from Study Events. It is a cache and must not be synchronized.
_Avoid_: Primary Database, Shared Database

**Question Cache**:
Device-local LeetCode problem metadata used for search and display. It can be refreshed by LeetCode Import and does not determine FSRS history.

**Daily Plan**:
The due-first bounded queue produced from active cards. By default it contains at most 20 cards and at most 5 new cards.

**Solver**:
An external process, normally Neovim with `leetcode.nvim`, launched while the TUI is suspended. Solving and review grading are deliberately separate actions.
