# Implementation Plan - Modern PostgreSQL Optimization

This plan outlines the multi-phase modernization of the Vibomat data layer to leverage advanced
PostgreSQL features for performance, search, and AI-driven discovery.

## Phase 1: Infrastructure & Database Extensions [checkpoint: 01202a4]

Enable the necessary PostgreSQL extensions in the development and production environments.

- [x] Task: Update `docker-compose.yml` to use a PostgreSQL image that supports `pgvector` or
      ensure the build process installs it. 5c2c887
- [x] Task: Create a migration to enable `pgvector` and `pg_trgm` extensions in the database. 3b874e1
- [x] Task: Verify extensions are active and accessible via a database client. 3b874e1
- [x] Task: Update `conductor/tech-stack.md` to reflect the new database extensions. 4d2f302
- [x] Task: Conductor - User Manual Verification 'Infrastructure & Extensions' (Protocol in
      workflow.md) 01202a4

## Phase 2: Hybrid Storage & JSONB Optimization (Archives) [checkpoint: 5a33049]

Optimize the storage and querying of playlist data within the `Archives` table.

- [x] Task: Create unit tests for querying specific fields within the `Archives` JSONB data. 51a7f1f
- [x] Task: Create a migration to analyze existing `Archives` data and ensure JSONB structures
      conform to expected indexing patterns. 4c4f031
- [x] Task: Implement GIN indices on the `Archives.playlist_data` (or equivalent) column for
      optimized key-value lookups. 1b39edb
- [x] Task: Refactor existing repository methods to use path-based JSONB queries where performance
      benefits are identified. d60580e
- [x] Task: (Research/Optional) Analyze table partitioning strategies for `Archives` based on
      `user_id` or `created_at`. c075a99
- [x] Task: Conductor - User Manual Verification 'JSONB Optimization' (Protocol in workflow.md) 5a33049

## Phase 3: Search & Discovery (Metadata)

Implement advanced search features for Artists and Tracks using FTS and Trigrams.

- [x] Task: Write unit tests for fuzzy search and full-text search requirements. 22fc7d3
- [x] Task: Create a migration to populate `tsvector` columns for existing Artist/Track records
      (backfill data). 836c942
- [x] Task: Create functional GIN indices for Full Text Search on Artist/Track names. 130b7a2
- [~] Task: Implement `pg_trgm` indices for fuzzy name matching.
- [ ] Task: Update the search service/API to leverage these new indexing strategies.
- [ ] Task: Conductor - User Manual Verification 'Search & Discovery' (Protocol in workflow.md)

## Phase 4: Vector Store Foundation (AI Logs)

Establish the database layer for storing and querying AI-generated embeddings.

- [ ] Task: Create unit tests for vector similarity search (top-k nearest neighbors).
- [ ] Task: Create the `AIInteractionEmbeddings` table with a `vector` column (dimension based on
      target model, e.g., 768 or 1536).
- [ ] Task: Create a data migration strategy (or script) to generate and store embeddings for
      historical AI logs if applicable.
- [ ] Task: Implement HNSW or IVFFlat indices for efficient similarity searches.
- [ ] Task: Implement a basic repository method to store and retrieve nearest neighbor embeddings.
- [ ] Task: Conductor - User Manual Verification 'Vector Store Foundation' (Protocol in workflow.md)
