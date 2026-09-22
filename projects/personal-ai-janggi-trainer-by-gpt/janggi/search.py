from __future__ import annotations

from dataclasses import dataclass
import random
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


@dataclass(frozen=True)
class SearchConfig:
    depth: int = 2
    mobility_weight: int = 2
    quiescence_depth: int = 1
    root_refinement_count: int = 0
    random_ties: bool = False
    seed: Optional[int] = None

    def __post_init__(self) -> None:
        if self.depth < 1:
            raise ValueError("depth must be at least 1")
        if self.mobility_weight < 0:
            raise ValueError("mobility_weight must be non-negative")
        if self.quiescence_depth < 0:
            raise ValueError("quiescence_depth must be non-negative")
        if self.root_refinement_count < 0:
            raise ValueError("root_refinement_count must be non-negative")


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
            tuple[int, tuple[Move, ...]],
        ] = {}
        self._evaluation_cache: dict[tuple[object, ...], int] = {}
        self._check_cache: dict[tuple[tuple[object, ...], Move], bool] = {}
        self._legal_moves_cache: dict[tuple[tuple[object, ...], bool], tuple[Move, ...]] = {}
        self._active_search_depth = self.config.depth
        self._shallow_node_count = 0

    @property
    def info(self) -> EngineInfo:
        return EngineInfo(name="negamax", version="4")

    def choose_move(self, state: GameState) -> Move:
        analysis = self.analyze(state)
        if analysis.best_move is None:
            raise ValueError("position has no legal move")
        return validate_engine_move(self, state, analysis.best_move)

    def analyze(self, state: GameState) -> EngineAnalysis:
        self._nodes = 0
        self._transposition.clear()
        self._evaluation_cache.clear()
        self._check_cache.clear()
        self._legal_moves_cache.clear()
        moves = self._ordered_moves(state, self._legal_moves(state, include_pass=False))
        if not moves:
            if self._legal_moves(state, include_pass=True):
                move = Move.pass_move()
                return EngineAnalysis(
                    best_move=move,
                    score_cp=self._evaluate(state),
                    depth=self.config.depth,
                    nodes=self._nodes,
                    principal_variation=(move,),
                    perspective=state.turn,
                )
            return EngineAnalysis(
                best_move=None,
                score_cp=-MATE_SCORE if state.is_in_check(state.turn) else 0,
                depth=self.config.depth,
                nodes=self._nodes,
                principal_variation=(),
                perspective=state.turn,
            )

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

    def _search(
        self,
        state: GameState,
        depth: int,
        alpha: int,
        beta: int,
        noisy: bool = False,
    ) -> tuple[int, tuple[Move, ...]]:
        self._nodes += 1
        cache_key = (state.position_key(), depth, noisy)
        cached = self._transposition.get(cache_key)
        if cached is not None:
            return cached

        moves = self._ordered_moves(state, self._legal_moves(state, include_pass=False))
        if not moves:
            if state.is_in_check(state.turn):
                # Mate distance must depend only on search depth, not the
                # historical move count. The latter is intentionally excluded
                # from position_key(), so it cannot safely affect a cached value.
                mate_distance = self._active_search_depth - max(depth, 0)
                result = (-MATE_SCORE + mate_distance, ())
            else:
                result = (self._evaluate(state), ())
            self._transposition[cache_key] = result
            return result

        if depth <= 0:
            if noisy and self.config.quiescence_depth > 0:
                result = self._quiescence(
                    state,
                    self.config.quiescence_depth,
                    alpha,
                    beta,
                )
            else:
                result = (self._evaluate(state), ())
            self._transposition[cache_key] = result
            return result

        best_score = -MATE_SCORE * 2
        best_pv: tuple[Move, ...] = ()
        cutoff = False
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
                cutoff = True
                break

        # Only cache fully searched nodes. A cutoff value is a bound, not an
        # exact minimax result, and therefore must not be reused as one.
        result = (best_score, best_pv)
        if not cutoff:
            self._transposition[cache_key] = result
        return result

    def _quiescence(
        self,
        state: GameState,
        depth: int,
        alpha: int,
        beta: int,
    ) -> tuple[int, tuple[Move, ...]]:
        """Extend only short forcing sequences after a noisy move."""
        self._nodes += 1
        stand_pat = self._evaluate(state)

        if depth <= 0:
            return stand_pat, ()

        in_check = state.is_in_check(state.turn)
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

        best_score = stand_pat
        best_pv: tuple[Move, ...] = ()
        if stand_pat >= beta:
            return stand_pat, ()
        alpha = max(alpha, stand_pat)

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
            if score > best_score:
                best_score = score
                best_pv = (move,) + child_pv
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break

        return best_score, best_pv

    def _ordered_moves(self, state: GameState, moves: tuple[Move, ...]) -> tuple[Move, ...]:
        """Prioritize captures, then checks, then stable source/destination order."""
        return tuple(
            sorted(
                moves,
                key=lambda move: (
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
    def _activity_score(side: Side, moves: tuple[Move, ...]) -> int:
        score = 0
        # Use the already-generated legal move list, avoiding a second move
        # generation pass solely for the activity evaluation.
        for move in moves:
            if move.is_pass or move.src is None:
                continue
            piece = None
            # The caller's move list is generated from the corresponding side's
            # position, so the piece kind is recovered by the source square in
            # the helper below rather than by creating a new state.
            # This method is replaced by _activity_score_for_state when the
            # board is available; kept private and intentionally unused here.
            _ = piece
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
