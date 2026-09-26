# ADR 003: Official FSRS and external solver boundaries

Status: accepted

## Context

The app should plan memory reviews without duplicating a maintained scheduler or becoming another LeetCode code editor.

## Decision

Use official `py-fsrs` with Again, Hard, Good, and Easy. Accepted imports enroll cards without manufacturing a review. Disable scheduling fuzz during event replay for deterministic multi-device projections.

Suspend the TUI while running a device-local solver command. The default opens the `leetcode.nvim` dashboard through `nvim +Leet`; placeholders and environment variables provide a generic contract for other solvers. Returning from a solver does not imply success—the user explicitly grades or skips.

## Consequences

LeetCode API changes, editor plugin changes, and scheduling changes stay behind separate adapters. Users can replace the solver without changing study history.
