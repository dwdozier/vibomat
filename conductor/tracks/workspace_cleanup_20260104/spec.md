# Track Specification: AI Workspace Cleanup and Conductor Standardization

## Overview

This track focuses on consolidating all AI instructions and project context into the Conductor
framework. By migrating content from the legacy `GEMINI.md` and incorporating lessons learned from
early usage, we will establish Conductor as the single source of truth for AI interactions within
the Vibomat project.

## Functional Requirements

* **Content Migration:**
  * Extract "Project Summary" and "Vib-O-Mat Terminology" into `conductor/product.md`.
  * Extract "Core Architecture" and "Coding Standards" into `conductor/tech-stack.md`.
  * Populate/Update `conductor/code_styleguides/python.md` and
    `conductor/code_styleguides/typescript.md` with relevant standards from `GEMINI.md`.
  * Extract "Critical Rules," "Key Commands," and "Branching Strategy" into `conductor/workflow.md`.
* **Protocol Formalization:**
  * Define a clear "Phase Completion Verification and Checkpointing Protocol" in
    `conductor/workflow.md`.
* **Testing Documentation:**
  * Explicitly document the use of Pytest (backend) and Playwright (frontend/E2E) in
    `conductor/tech-stack.md`.
* **Workspace Cleanup:**
  * Delete the project-level `GEMINI.md` file after successful migration.
  * Delete the `planning/` directory and its contents.

## Non-Functional Requirements

* **Consistency:** Ensure that the migrated rules align with existing Conductor philosophy
  (spec-driven, iterative).
* **Clarity:** Use clear, imperative language for rules and protocols.

## Acceptance Criteria

1. All useful directives from `GEMINI.md` (and known global directives) are represented in the
   `conductor/` directory.
2. `conductor/workflow.md` contains a usable "Phase Completion" protocol.
3. `conductor/tech-stack.md` includes explicit testing framework details.
4. `GEMINI.md` is removed from the repository.
5. `planning/` directory is removed.
6. A status check (`/conductor:status`) reflects a clean, Conductor-standard project.

## Out of Scope

* Updating external documentation (e.g., `README.md`) unless directly impacted by the migration of
  rules.
