# Tactical analysis boundary

## Current role

`janggi.analysis` provides domain-level tactical signals that are intentionally independent of any particular engine implementation.

The current detector answers two bounded questions after a played move:

1. Can the opponent immediately capture the moved piece, and can the mover immediately recapture on that destination?
2. Can the opponent make one reply after which the mover has a next-turn double-attack opportunity against at least two non-general pieces of at least guard value?

Immediate capture is represented by `TacticalRisk`:

- `none`: no immediate capture is available
- `immediate_capture`: an immediate capture exists, but every such capture has an immediate legal recapture
- `hanging_piece`: at least one immediate capture exists with no immediate legal recapture

The bounded multi-ply signal is represented separately by `TacticalMotif`:

- `double_attack`: after one opponent reply, the mover has legal captures against at least two non-general opposing pieces worth at least a guard, without considering the mover's intervening defensive resources

This is a threat signal, not a proof that the move is losing. It is kept separate from engine score and does not change the existing score-based severity classification.

## Coaching interpretation

Coaching keeps tactical structure and engine evaluation as separate signals:

- `hanging_piece` takes priority because the detector found a concrete immediate tactical vulnerability.
- `immediate_capture` changes the explanation, but severity still follows the engine score; a capturable piece is not automatically a bad move when the exchange is protected.
- `double_attack` adds a forward-looking warning without changing score-based severity.
- `none` leaves the normal score-based classification in control.

This separation prevents the current bounded detector from pretending to be a stronger tactical engine.

## Fixture coverage

The regression suite keeps representative positions for:

- clean captures with no destination attack
- protected exchanges where the moved piece can be captured and immediately recaptured
- unprotected moved pieces that are left hanging
- positions without an immediate capture, to prevent speculative immediate-risk labeling
- a bounded next-turn double-attack threat from the mover's perspective
- pass moves with no tactical motif
- coaching messages that expose tactical signals without changing the score-based classification

Check detection remains covered independently through `MoveAnalysis.gives_check`.

## Explicit boundary

The current tactical motif detector is intentionally narrow. It does not currently classify:

- forced forks that require considering the mover's defensive reply
- pins and discovered attacks that unfold over multiple plies
- deflections, zwischenzug, or attraction motifs
- sacrificial moves justified by a later tactical sequence
- global exchange quality based on deeper search

Those belong in a future stronger tactical-analysis layer. Any expansion should remain separate from the domain legality model and should expose uncertainty rather than silently upgrading a bounded heuristic into a strong tactical claim.
