from __future__ import annotations

from dataclasses import dataclass
import random
from time import monotonic
from typing import Optional

from .core import GameState, Move, PieceType, Side, palace_for
from .engine import EngineAnalysis, EngineInfo, validate_engine_move


# Reference material ordering is calibrated to common Janggi point systems:
# chariot 13, cannon 7, horse 5, elephant 3, guard 3, soldier 2.
# The absolute scale remains compatible with the existing mate score.
PIECE_VALUES = {
    PieceType.GENERAL: 10_000,
    PieceType.CHARIOT: 1_300,
    PieceType.CANNON: 700,
    PieceType.ELEPHANT: 300,
    PieceType.HORSE: 500,
    PieceType.GUARD: 300,
    PieceType.SOLDIER: 200,
}
MATE_SCORE = 100_000

CHECK_BONUS = 120
GUARD_PALACE_BONUS = 18
SOLDIER_ADVANCE_BONUS = 12
SOLDIER_CENTER_BONUS = 8

# Small strategic terms layered on top of material and raw mobility.
# These are deliberately much smaller than piece values so tactical material
# changes remain dominant while activity and safety can break quiet ties.
PIECE_ACTIVITY_WEIGHTS = {
    PieceType.GENERAL: 0,
    PieceType.CHARIOT: 3,
    PieceType.CANNON: 2,
    PieceType.HORSE: 2,
    PieceType.ELEPHANT: 1,
    PieceType.GUARD: 1,
    PieceType.SOLDIER: 1,
}
ACTIVITY_BONUS = 2
TACTICAL_PRESSURE_DIVISOR = 25
PALACE_PRESSURE_BONUS = 5


class _SearchTimeout(Exception):
    """Internal control flow for a time-budgeted iterative search."""


@dataclass(frozen=True)
class _TranspositionEntry:
    score: int
    principal_variation: tuple[Move, ...]
    bound: str


_TT_EXACT = "exact"
_TT_LOWER = "lower"
_TT_UPPER = "upper"


@dataclass(frozen=True)
class SearchConfig:
    depth: int = 2
    mobility_weight: int = 2
    quiescence_depth: int = 1
    root_refinement_count: int = 0
    random_ties: bool = False
    seed: Optional[int] = None
    time_limit_ms: Optional[int] = None
    adaptive_ordering: bool = True
    quiescence_check_extension: bool = True

    def __post_init__(self) -> None:
        if self.depth < 1:
            raise ValueError("depth must be at least 1")
        if self.mobility_weight < 0:
            raise ValueError("mobility_weight must be non-negative")
        if self.quiescence_depth < 0:
            raise ValueError("quiescence_depth must be non-negative")
        if self.root_refinement_count < 0:
            raise ValueError("root_refinement_count must be non-negative")
        if self.time_limit_ms is not None:
            if (
                not isinstance(self.time_limit_ms, int)
                or isinstance(self.time_limit_ms, bool)
                or self.time_limit_ms < 1
            ):
                raise ValueError("time_limit_ms must be a positive integer when provided")
        if not isinstance(self.adaptive_ordering, bool):
            raise ValueError("adaptive_ordering must be a boolean")
        if not isinstance(self.quiescence_check_extension, bool):
            raise ValueError("quiescence_check_extension must be a boolean")


class NegamaxEngine:
    """Dependency-free depth-limited Janggi search backend.

    Authoritative move legality remains in GameState. This engine supplies a
    deterministic material/mobility/positional evaluation and alpha-beta negamax search.
    Optional root-level random tie breaking can add self-play diversity without
    changing the default deterministic behavior.
    """

    def __init__(self, config: Optional[SearchConfig] = None) -> None:
        self.config = config or SearchConfig()
        self._nodes = 0
        self._rng = random.Random(self.config.seed)
        self._transposition: dict[
            tuple[tuple[object, ...], int, bool],
            _TranspositionEntry,
        ] = {}
        self._tt_hits = 0
        self._tt_cutoffs = 0
        self._killer_moves: dict[int, list[Move]] = {}
        self._history_scores: dict[tuple[Side, Move], int] = {}
        self._killer_hits = 0
        self._history_hits = 0
        self._evaluation_cache: dict[tuple[object, ...], int] = {}
        self._check_cache: dict[tuple[tuple[object, ...], Move], bool] = {}
        self._legal_moves_cache: dict[tuple[tuple[object, ...], bool], tuple[Move, ...]] = {}
        self._active_search_depth = self.config.depth
        self._shallow_node_count = 0
        self._deadline: Optional[float] = None

    @property
    def info(self) -> EngineInfo:
        return EngineInfo(name="negamax", version="7")

    def choose_move(self, state: GameState) -> Move:
        analysis = self.analyze(state)
        if analysis.best_move is None:
            raise ValueError("position has no legal move")
        return validate_engine_move(self, state, analysis.best_move)

    def analyze(self, state: GameState) -> EngineAnalysis:
        self._nodes = 0
        self._tt_hits = 0
        self._tt_cutoffs = 0
        self._killer_hits = 0
        self._history_hits = 0
        self._transposition.clear()
        self._killer_moves.clear()
        self._history_scores.clear()
        self._evaluation_cache.clear()
        self._check_cache.clear()
        self._legal_moves_cache.clear()

        if self.config.time_limit_ms is not None:
            self._deadline = monotonic() + (self.config.time_limit_ms / 1000.0)

        try:
            if self._is_consecutive_pass_draw(state):
                return EngineAnalysis(
                    best_move=None,
                    score_cp=0,
                    depth=0,
                    nodes=self._nodes,
                    principal_variation=(),
                    perspective=state.turn,
                )

            # The time budget includes root move generation and ordering, not
            # just the recursive alpha-beta search.
            legal_moves = self._legal_moves(state, include_pass=True)
            if not legal_moves:
                return EngineAnalysis(
                    best_move=None,
                    score_cp=-MATE_SCORE if state.is_in_check(state.turn) else 0,
                    depth=self.config.depth,
                    nodes=self._nodes,
                    principal_variation=(),
                    perspective=state.turn,
                )
            if self._deadline_expired():
                return self._fallback_analysis(state, legal_moves)

            moves = self._ordered_search_moves(
                state,
                legal_moves,
                preferred_move=None,
                depth=self._active_search_depth,
            )
            if self._deadline_expired():
                return self._fallback_analysis(state, moves)

            if self.config.time_limit_ms is not None:
                return self._analyze_iterative_deepening(state, moves)

            best_score = -MATE_SCORE * 2
            best_results: list[tuple[Move, tuple[Move, ...]]] = []
            alpha = -MATE_SCORE * 2
            self._shallow_node_count = 0
            beta = MATE_SCORE * 2

            shallow_results: list[tuple[int, int, Move, tuple[Move, ...]]] = []
            self._active_search_depth = self.config.depth
            for index, move in enumerate(moves):
                child = state.apply(move)
                child_noisy = self._captured_value(state, move) > 0 or self._gives_check(state, move)
                child_score, child_pv = self._search(
                    child,
                    self.config.depth - 1,
                    -beta,
                    -alpha,
                    child_noisy,
                )
                score = -child_score
                shallow_results.append((score, index, move, (move,) + child_pv))
                if score > best_score:
                    best_score = score
                    best_results = [(move, (move,) + child_pv)]
                elif score == best_score:
                    best_results.append((move, (move,) + child_pv))
                alpha = max(alpha, score)

            self._shallow_node_count = self._nodes
            if self.config.root_refinement_count > 0:
                finalists = sorted(
                    shallow_results,
                    key=lambda item: (-item[0], item[1]),
                )[: self.config.root_refinement_count]
                refined_results: list[tuple[int, int, Move, tuple[Move, ...]]] = []
                refinement_nodes = 0
                for _, shallow_rank, move, _ in finalists:
                    self._transposition.clear()
                    self._evaluation_cache.clear()
                    self._check_cache.clear()
                    self._legal_moves_cache.clear()
                    self._nodes = 0
                    self._active_search_depth = self.config.depth + 1
                    child = state.apply(move)
                    child_noisy = self._captured_value(state, move) > 0 or self._gives_check(state, move)
                    child_score, child_pv = self._search(
                        child,
                        self.config.depth,
                        -MATE_SCORE * 2,
                        MATE_SCORE * 2,
                        child_noisy,
                    )
                    refinement_nodes += self._nodes
                    refined_results.append((-child_score, shallow_rank, move, (move,) + child_pv))

                total_refinement_results = sorted(
                    refined_results,
                    key=lambda item: (-item[0], item[1]),
                )
                if total_refinement_results:
                    best_score, _, best_move, best_pv = total_refinement_results[0]
                    if len(total_refinement_results) > 1:
                        tied = [item for item in total_refinement_results if item[0] == best_score]
                        if self.config.random_ties and len(tied) > 1:
                            best_score, _, best_move, best_pv = self._rng.choice(tied)
                    self._nodes = self._shallow_node_count + refinement_nodes
                    return EngineAnalysis(
                        best_move=best_move,
                        score_cp=best_score,
                        depth=self.config.depth + 1,
                        nodes=self._nodes,
                        principal_variation=best_pv,
                        perspective=state.turn,
                    )

            if self.config.random_ties and len(best_results) > 1:
                best_move, best_pv = self._rng.choice(best_results)
            else:
                best_move, best_pv = best_results[0]

            self._active_search_depth = self.config.depth
            return EngineAnalysis(
                best_move=best_move,
                score_cp=best_score,
                depth=self.config.depth,
                nodes=self._nodes,
                principal_variation=best_pv,
                perspective=state.turn,
            )
        finally:
            self._deadline = None

    def _fallback_analysis(self, state: GameState, moves: tuple[Move, ...]) -> EngineAnalysis:
        move = moves[0]
        return EngineAnalysis(
            best_move=move,
            score_cp=None,
            depth=0,
            nodes=self._nodes,
            principal_variation=(move,),
            perspective=state.turn,
        )

    def _analyze_iterative_deepening(
        self,
        state: GameState,
        moves: tuple[Move, ...],
    ) -> EngineAnalysis:
        """Search completed depths until the budget expires."""
        assert self.config.time_limit_ms is not None
        assert self._deadline is not None
        best_analysis: Optional[EngineAnalysis] = None
        preferred_move: Optional[Move] = None

        for depth in range(1, self.config.depth + 1):
            if depth > 1:
                self._transposition.clear()
            self._active_search_depth = depth
            try:
                score, best_move, best_pv = self._search_root(
                    state,
                    moves,
                    depth,
                    preferred_move,
                )
            except _SearchTimeout:
                break

            best_analysis = EngineAnalysis(
                best_move=best_move,
                score_cp=score,
                depth=depth,
                nodes=self._nodes,
                principal_variation=best_pv,
                perspective=state.turn,
            )
            preferred_move = best_move

            if abs(score) >= MATE_SCORE - self.config.depth:
                break

        if best_analysis is not None:
            return best_analysis

        fallback = moves[0]
        return EngineAnalysis(
            best_move=fallback,
            score_cp=None,
            depth=0,
            nodes=self._nodes,
            principal_variation=(fallback,),
            perspective=state.turn,
        )

    def _search_root(
        self,
        state: GameState,
        moves: tuple[Move, ...],
        depth: int,
        preferred_move: Optional[Move],
        alpha: Optional[int] = None,
        beta: Optional[int] = None,
    ) -> tuple[int, Move, tuple[Move, ...]]:
        self._check_time_budget()
        ordered_moves = self._ordered_search_moves(
            state,
            moves,
            preferred_move,
            depth,
        )
        best_score = -MATE_SCORE * 2
        best_results: list[tuple[Move, tuple[Move, ...]]] = []
        alpha = -MATE_SCORE * 2 if alpha is None else alpha
        beta = MATE_SCORE * 2 if beta is None else beta

        for move in ordered_moves:
            self._check_time_budget()
            child = state.apply(move)
            child_noisy = self._captured_value(state, move) > 0 or self._gives_check(state, move)
            child_score, child_pv = self._search(
                child,
                depth - 1,
                -beta,
                -alpha,
                child_noisy,
            )
            score = -child_score
            candidate_pv = (move,) + child_pv
            if score > best_score:
                best_score = score
                best_results = [(move, candidate_pv)]
            elif score == best_score:
                best_results.append((move, candidate_pv))
            alpha = max(alpha, score)

        if self.config.random_ties and len(best_results) > 1:
            best_move, best_pv = self._rng.choice(best_results)
        else:
            best_move, best_pv = best_results[0]
        return best_score, best_move, best_pv

    def _check_time_budget(self) -> None:
        if self._deadline_expired():
            raise _SearchTimeout

    def _deadline_expired(self) -> bool:
        return self._deadline is not None and monotonic() >= self._deadline

    @staticmethod
    def _is_consecutive_pass_draw(state: GameState) -> bool:
        return (
            len(state.history) >= 2
            and state.history[-1].is_pass
            and state.history[-2].is_pass
        )

    def _search(
        self,
        state: GameState,
        depth: int,
        alpha: int,
        beta: int,
        noisy: bool = False,
    ) -> tuple[int, tuple[Move, ...]]:
        self._check_time_budget()
        self._nodes += 1
        if self._is_consecutive_pass_draw(state):
            return 0, ()

        original_alpha = alpha
        original_beta = beta
        cache_key = (state.position_key(), depth, noisy)
        cached = self._transposition.get(cache_key)
        preferred_move: Optional[Move] = None
        if cached is not None:
            self._tt_hits += 1
            if cached.bound == _TT_EXACT:
                return cached.score, cached.principal_variation
            if cached.bound == _TT_LOWER and cached.score >= beta:
                self._tt_cutoffs += 1
                return cached.score, cached.principal_variation
            if cached.bound == _TT_UPPER and cached.score <= alpha:
                self._tt_cutoffs += 1
                return cached.score, cached.principal_variation
            if cached.principal_variation:
                preferred_move = cached.principal_variation[0]

        moves = self._ordered_search_moves(
            state,
            self._legal_moves(state, include_pass=True),
            preferred_move,
            depth,
        )
        if not moves:
            if state.is_in_check(state.turn):
                # Mate distance must depend only on search depth, not the
                # historical move count. The latter is intentionally excluded
                # from position_key(), so it cannot safely affect a cached value.
                mate_distance = self._active_search_depth - max(depth, 0)
                result = (-MATE_SCORE + mate_distance, ())
            else:
                result = (self._evaluate(state), ())
            self._transposition[cache_key] = _TranspositionEntry(
                score=result[0], principal_variation=result[1], bound=_TT_EXACT
            )
            return result

        if depth <= 0:
            if noisy and self.config.quiescence_depth > 0:
                result = self._quiescence(
                    state,
                    self.config.quiescence_depth,
                    alpha,
                    beta,
                )
                bound = self._transposition_bound(result[0], original_alpha, original_beta)
            else:
                result = (self._evaluate(state), ())
                bound = _TT_EXACT
            self._transposition[cache_key] = _TranspositionEntry(
                score=result[0], principal_variation=result[1], bound=bound
            )
            return result

        best_score = -MATE_SCORE * 2
        best_pv: tuple[Move, ...] = ()
        for move in moves:
            child = state.apply(move)
            child_noisy = self._captured_value(state, move) > 0 or self._gives_check(state, move)
            child_score, child_pv = self._search(
                child,
                depth - 1,
                -beta,
                -alpha,
                child_noisy,
            )
            score = -child_score
            if not best_pv or score > best_score:
                best_score = score
                best_pv = (move,) + child_pv
            if score > alpha:
                alpha = score
            if alpha >= beta:
                self._record_cutoff_heuristics(state, move, depth)
                break

        bound = self._transposition_bound(best_score, original_alpha, original_beta)
        self._transposition[cache_key] = _TranspositionEntry(
            score=best_score,
            principal_variation=best_pv,
            bound=bound,
        )
        return best_score, best_pv

    @staticmethod
    def _transposition_bound(score: int, alpha: int, beta: int) -> str:
        if score <= alpha:
            return _TT_UPPER
        if score >= beta:
            return _TT_LOWER
        return _TT_EXACT

    def _ordered_search_moves(
        self,
        state: GameState,
        moves: tuple[Move, ...],
        preferred_move: Optional[Move],
        depth: int,
    ) -> tuple[Move, ...]:
        ordered = self._ordered_moves(state, moves)
        if not self.config.adaptive_ordering or not getattr(self, "_adaptive_ordering_enabled", True):
            return ordered

        ply = max(self._active_search_depth - depth, 0)
        killers = self._killer_moves.get(ply, ())
        killer_rank = {move: index for index, move in enumerate(killers)}

        def ordering_key(move: Move) -> tuple[object, ...]:
            is_preferred = 0 if preferred_move is not None and move == preferred_move else 1
            capture_value = self._captured_value(state, move)
            gives_check = int(self._gives_check(state, move))
            killer_index = killer_rank.get(move, len(killers))
            history = self._history_scores.get((state.turn, move), 0)
            if killer_index < len(killers):
                self._killer_hits += 1
            elif history:
                self._history_hits += 1
            return (
                is_preferred,
                int(move.is_pass),
                -capture_value,
                -gives_check,
                killer_index,
                -history,
                move.src is None,
                move.src or (-1, -1),
                move.dst or (-1, -1),
            )

        return tuple(sorted(ordered, key=ordering_key))

    def _record_cutoff_heuristics(
        self,
        state: GameState,
        move: Move,
        depth: int,
    ) -> None:
        if self._captured_value(state, move) > 0 or self._gives_check(state, move):
            return

        ply = max(self._active_search_depth - depth, 0)
        killers = self._killer_moves.setdefault(ply, [])
        if move in killers:
            killers.remove(move)
        killers.insert(0, move)
        del killers[2:]

        history_key = (state.turn, move)
        bonus = max(depth, 1) * max(depth, 1)
        self._history_scores[history_key] = min(
            1_000_000,
            self._history_scores.get(history_key, 0) + bonus,
        )

    def _quiescence(
        self,
        state: GameState,
        depth: int,
        alpha: int,
        beta: int,
    ) -> tuple[int, tuple[Move, ...]]:
        """Extend short forcing sequences while never standing pat in check."""
        self._check_time_budget()
        self._nodes += 1
        stand_pat = self._evaluate(state)
        in_check = state.is_in_check(state.turn)

        # A side in check has no legal stand-pat value: it must make a move.
        # Even when the nominal quiescence budget is exhausted, extend one
        # check-evasion ply so the search never evaluates an illegal position
        # as if it were a legal quiet leaf.
        if depth <= 0 and (not in_check or not self.config.quiescence_check_extension):
            return stand_pat, ()

        if in_check:
            moves = self._ordered_moves(
                state,
                self._legal_moves(state, include_pass=False),
            )
        else:
            moves = tuple(
                move
                for move in self._ordered_moves(
                    state,
                    self._legal_moves(state, include_pass=False),
                )
                if self._captured_value(state, move) > 0 or self._gives_check(state, move)
            )

        if not moves:
            if in_check:
                return -MATE_SCORE, ()
            return stand_pat, ()

        if in_check:
            best_score = -MATE_SCORE * 2
        else:
            best_score = stand_pat
            if stand_pat >= beta:
                return stand_pat, ()
            alpha = max(alpha, stand_pat)

        best_pv: tuple[Move, ...] = ()
        for move in moves:
            child = state.apply(move)
            child_noisy = self._captured_value(state, move) > 0 or self._gives_check(state, move)
            if child_noisy and depth > 1:
                child_score, child_pv = self._quiescence(
                    child,
                    depth - 1,
                    -beta,
                    -alpha,
                )
            else:
                child_score, child_pv = self._evaluate(child), ()
            score = -child_score
            if not best_pv or score > best_score:
                best_score = score
                best_pv = (move,) + child_pv
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break

        return best_score, best_pv

    _adaptive_ordering_enabled = True

    def _ordered_moves(
        self,
        state: GameState,
        moves: tuple[Move, ...],
        preferred_move: Optional[Move] = None,
    ) -> tuple[Move, ...]:
        """Prioritize a previous-PV move, then captures, checks, and stable order."""
        return tuple(
            sorted(
                moves,
                key=lambda move: (
                    0 if preferred_move is not None and move == preferred_move else 1,
                    int(move.is_pass),
                    -self._captured_value(state, move),
                    -int(self._gives_check(state, move)),
                    move.src or (-1, -1),
                    move.dst or (-1, -1),
                ),
            )
        )

    @staticmethod
    def _captured_value(state: GameState, move: Move) -> int:
        if move.is_pass or move.dst is None:
            return 0
        target = state.piece_at(move.dst)
        return PIECE_VALUES[target.kind] if target is not None else 0

    def _gives_check(self, state: GameState, move: Move) -> bool:
        if move.is_pass:
            return False
        cache_key = (state.position_key(), move)
        cached = self._check_cache.get(cache_key)
        if cached is not None:
            return cached
        result = state.apply(move).is_in_check(state.turn.opponent)
        self._check_cache[cache_key] = result
        return result

    def _legal_moves(self, state: GameState, include_pass: bool) -> tuple[Move, ...]:
        cache_key = (state.position_key(), include_pass)
        cached = self._legal_moves_cache.get(cache_key)
        if cached is not None:
            return cached
        moves = state.legal_moves(include_pass=include_pass)
        self._legal_moves_cache[cache_key] = moves
        return moves

    def _evaluate(self, state: GameState) -> int:
        position_key = state.position_key()
        cached = self._evaluation_cache.get(position_key)
        if cached is not None:
            return cached

        own_material = 0
        opp_material = 0
        for piece in state.board:
            if piece is None:
                continue
            value = PIECE_VALUES[piece.kind]
            if piece.side is state.turn:
                own_material += value
            else:
                opp_material += value

        own_legal_moves = self._legal_moves(state, include_pass=False)
        opponent_state = GameState(board=state.board, turn=state.turn.opponent, history=state.history)
        opponent_legal_moves = self._legal_moves(opponent_state, include_pass=False)
        own_mobility = len(own_legal_moves)
        opponent_mobility = len(opponent_legal_moves)
        score = (own_material - opp_material) + self.config.mobility_weight * (
            own_mobility - opponent_mobility
        )

        score += self._positional_score(state, state.turn)

        own_activity = self._activity_score_for_state(state, state.turn, own_legal_moves)
        opponent_activity = self._activity_score_for_state(opponent_state, state.turn.opponent, opponent_legal_moves)
        score += ACTIVITY_BONUS * (own_activity - opponent_activity)

        own_pressure = self._capture_pressure(own_legal_moves, state)
        opponent_pressure = self._capture_pressure(opponent_legal_moves, opponent_state)
        score += own_pressure - opponent_pressure

        own_vulnerability = self._capture_pressure(opponent_legal_moves, opponent_state)
        opponent_vulnerability = self._capture_pressure(own_legal_moves, state)
        score -= own_vulnerability // 2
        score += opponent_vulnerability // 2

        own_palace_pressure = self._palace_pressure(own_legal_moves, state.turn.opponent)
        opponent_palace_pressure = self._palace_pressure(opponent_legal_moves, state.turn)
        score += own_palace_pressure - opponent_palace_pressure

        if state.is_in_check(state.turn):
            score -= CHECK_BONUS
        if state.is_in_check(state.turn.opponent):
            score += CHECK_BONUS

        self._evaluation_cache[position_key] = score
        return score

    @staticmethod
    def _activity_score_for_state(
        state: GameState,
        side: Side,
        moves: tuple[Move, ...],
    ) -> int:
        score = 0
        for move in moves:
            if move.is_pass or move.src is None:
                continue
            piece = state.piece_at(move.src)
            if piece is not None and piece.side is side:
                score += PIECE_ACTIVITY_WEIGHTS[piece.kind]
        return score

    @staticmethod
    def _capture_pressure(
        moves: tuple[Move, ...],
        state: GameState,
    ) -> int:
        captured = 0
        for move in moves:
            if move.is_pass or move.dst is None:
                continue
            target = state.piece_at(move.dst)
            if target is None or target.kind is PieceType.GENERAL:
                continue
            captured += PIECE_VALUES[target.kind]
        return captured // TACTICAL_PRESSURE_DIVISOR

    @staticmethod
    def _palace_pressure(
        moves: tuple[Move, ...],
        target_side: Side,
    ) -> int:
        palace = palace_for(target_side)
        pressured_points = sum(
            1
            for move in moves
            if not move.is_pass and move.dst in palace
        )
        return pressured_points * PALACE_PRESSURE_BONUS

    @staticmethod
    def _positional_score(state: GameState, side: Side) -> int:
        """Evaluate bounded positional terms from both sides' perspective."""
        score = 0
        opponent = side.opponent

        for y in range(10):
            for x in range(9):
                piece = state.board[y * 9 + x]
                if piece is None or piece.side not in (side, opponent):
                    continue

                sign = 1 if piece.side is side else -1

                if piece.kind is PieceType.SOLDIER:
                    progress = (y - 3) if piece.side is Side.CHO else (6 - y)
                    soldier_score = max(progress, 0) * SOLDIER_ADVANCE_BONUS
                    distance_from_center = abs(x - 4)
                    if distance_from_center == 0:
                        soldier_score += SOLDIER_CENTER_BONUS
                    elif distance_from_center == 1:
                        soldier_score += SOLDIER_CENTER_BONUS // 2
                    score += sign * soldier_score

                elif piece.kind is PieceType.GUARD:
                    if (3 <= x <= 5) and (
                        (piece.side is Side.CHO and 0 <= y <= 2)
                        or (piece.side is Side.HAN and 7 <= y <= 9)
                    ):
                        score += sign * GUARD_PALACE_BONUS

        return score
