# Track Specification: Preemptive Formatting Compliance

## Overview

To improve development efficiency and reduce friction caused by pre-commit hook failures, we will
update the project's operational guidelines. The goal is to instruct AI agents (and developers) to
proactively adhere to formatting standards—specifically line lengths and trailing newlines—during
the code generation and editing process, rather than relying on `pre-commit` to fix them after the
fact.

## Functional Requirements

* **Update `conductor/workflow.md`:**
  * Add a specific instruction in the "Guiding Principles" or "Critical Rules" section emphasizing
        "Right First Time" formatting.
  * Explicitly mention the 100-character line limit for both code and markdown.
  * Explicitly mention the requirement for a single trailing newline in all files.
* **Update `conductor/tech-stack.md`:**
  * Refine the "Coding Standards" section to reinforce that tools like `black` and `ruff` are
        validators, but the initial output should aim to be compliant.

## Non-Functional Requirements

* **Clarity:** The instructions must be unambiguous so that future AI contexts essentially "know"
    to format correctly before hitting save.

## Acceptance Criteria

1. `conductor/workflow.md` contains a clear directive about preemptive formatting.
2. `conductor/tech-stack.md` reinforces this philosophy.
3. A status check reflects the completion of these documentation updates.

## Out of Scope

* Configuring new linters (we are optimizing adherence to existing ones).
