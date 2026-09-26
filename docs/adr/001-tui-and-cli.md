# ADR 001: Textual TUI with Typer administration CLI

Status: accepted

## Context

The former Click CLI made a guided review session cumbersome, but scripts and recovery operations still need a stable non-interactive surface.

## Decision

Use Textual for the primary Today, Questions, Stats, Data, and Settings experience. Use Typer for initialization, imports, inspection, configuration, and direct rating/card operations. Both call the same `ApplicationService`.

The installed distribution and executable are both named `leetcode-fsrs`. The old `lcf` alias is removed.

## Consequences

Business rules cannot depend on Textual widgets or Typer contexts. TUI behavior can be exercised with Textual's test pilot, while scripts can use CLI commands and JSON output.
