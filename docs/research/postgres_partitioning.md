# Research: PostgreSQL Table Partitioning for Archives (Playlists)

## Goal

Evaluate the benefits and costs of implementing table partitioning for the `playlist` table.

## Strategies Evaluated

### 1. Partition by `user_id` (List Partitioning)

- **Pros:** Excellent data locality for the most common query pattern (fetch my playlists). Easier
  data deletion (GDPR compliance).
- **Cons:** Complex to manage as users grow. Requires a partition for every user or a grouping
  logic.

### 2. Partition by `created_at` (Range Partitioning)

- **Pros:** Good for aging out old data. Keeps recent (active) data in smaller, faster indices.
- **Cons:** Not aligned with primary query patterns (queries are usually user-scoped, not
  time-scoped across all users).

## Recommendation

**DEFER implementation.**
The current `playlist` table is expected to stay well under 10M rows in the near term. Standard
B-Tree indices on `user_id` and our new GIN index on `content_json` provide sub-millisecond lookups
at this scale. Partitioning adds significant complexity to migrations and foreign key management
(which has specific limitations in partitioned tables).

## Future Trigger

Re-evaluate if:

1. The table exceeds 100M rows.
2. `VACUUM` operations on the table begin to impact performance.
3. Multi-tenant requirements demand physical isolation.
