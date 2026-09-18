# Model Registry

`janggi.model` defines the application-level metadata contract for selectable AI models.

## ModelSpec

`ModelSpec` identifies a model with:

- a stable `id`
- a user-facing `display_name`
- the backend `engine_name`
- an optional `engine_version`
- an optional numeric `rating`
- an optional `source` label

The registry stores metadata only. Engine instances remain separate so the application does not become coupled to a specific search or machine-learning backend.

## ModelRegistry

`ModelRegistry` provides validated registration and lookup in memory. Duplicate IDs are rejected, unknown IDs raise `KeyError`, and `list()` preserves registration order.

This is intentionally a metadata layer rather than persistence, model loading, or matchmaking. Those concerns can be added later without changing the engine protocol.
