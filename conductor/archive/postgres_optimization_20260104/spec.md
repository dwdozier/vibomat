# Track Specification: Modern PostgreSQL Optimization

## Overview

This track aims to modernize the Vibomat data layer by leveraging advanced PostgreSQL features.
The goal is to improve performance, enhance search capabilities, and prepare the infrastructure
for AI-driven vector search. This will be a multi-phase roll-out involving infrastructure
updates, schema migrations, and application logic enhancements.

## Functional Requirements

* **Infrastructure:**
  * Update `docker-compose.yml` and production configuration to support `pgvector`.
* **Performance & Storage (Archives):**
  * Optimize `JSONB` usage for playlist/archive data, ensuring efficient indexing of commonly
        queried fields within the JSON structure.
  * Analyze and implement table partitioning for `Archives` if volume projections justify it
        (e.g., by user or timestamp).
* **Search & Discovery (Metadata):**
  * Implement Full Text Search (FTS) for Artists and Tracks using `tsvector` and `tsquery`.
  * Implement Trigram indices (`pg_trgm`) to support fuzzy matching for robust search
        handling (e.g., typos).
* **AI Integration (Vectors):**
  * Create a schema for storing vector embeddings of user prompts/interactions.
  * Implement basic vector similarity search queries.

## Non-Functional Requirements

* **Backward Compatibility:** Migrations must be non-destructive to existing data.
* **Performance:** Search queries should return results in under 200ms.
* **Maintainability:** Database extensions must be documented in `tech-stack.md`.

## Acceptance Criteria

1. Local and Production environments successfully run PostgreSQL with `pgvector` enabled.
2. Playlist `JSONB` data is queryable via indexed paths.
3. A "fuzzy search" endpoint returns relevant tracks even with minor spelling errors.
4. A new table exists for embeddings, and a test script proves similarity search works.

## Out of Scope

* Full implementation of the AI feature that *uses* the embeddings (this track focuses on the
    *enabling* database layer).
