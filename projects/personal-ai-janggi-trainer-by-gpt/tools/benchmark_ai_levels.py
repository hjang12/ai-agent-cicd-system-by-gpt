from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path
from time import perf_counter

from janggi import AI_LEVELS, GameState, HeadToHeadTournament, Move, NegamaxEngine, Piece, PieceType, Side, ai_level_configuration_fingerprint
from janggi.match import GameStatus, Match, RuleSet
from janggi.engine import validate_engine_move

CALIBRATION_PROTOCOL_VERSION = 2

@dataclass(frozen=True)
class Fixture:
    name: str
    state: GameState


def _initial_fixture() -> Fixture:
    return Fixture("initial", GameState.initial())


def _capture_fixture() -> Fixture:
    board = [None] * 90
    board[4 + 1 * 9] = Piece(Side.CHO, PieceType.GENERAL)
    board[4 + 8 * 9] = Piece(Side.HAN, PieceType.GENERAL)
    board[0 + 3 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
    board[0 + 4 * 9] = Piece(Side.HAN, PieceType.SOLDIER)
    board[2 + 3 * 9] = Piece(Side.CHO, PieceType.HORSE)
    return Fixture("capture", GameState(tuple(board), turn=Side.CHO))


def _check_fixture() -> Fixture:
    board = [None] * 90
    board[0] = Piece(Side.CHO, PieceType.GENERAL)
    board[4 + 9 * 9] = Piece(Side.HAN, PieceType.GENERAL)
    board[0 + 3 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
    board[8] = Piece(Side.CHO, PieceType.HORSE)
    return Fixture("check", GameState(tuple(board), turn=Side.CHO))


def _endgame_fixture() -> Fixture:
    board = [None] * 90
    board[4 + 1 * 9] = Piece(Side.CHO, PieceType.GENERAL)
    board[2 + 4 * 9] = Piece(Side.CHO, PieceType.CHARIOT)
    board[4 + 5 * 9] = Piece(Side.CHO, PieceType.SOLDIER)
    board[4 + 8 * 9] = Piece(Side.HAN, PieceType.GENERAL)
    board[6 + 6 * 9] = Piece(Side.HAN, PieceType.CHARIOT)
    board[4 + 6 * 9] = Piece(Side.HAN, PieceType.SOLDIER)
    board[3 + 9 * 9] = Piece(Side.HAN, PieceType.GUARD)
    return Fixture("endgame", GameState(tuple(board), turn=Side.CHO))




def _source_revision() -> str | None:
    revision = os.environ.get("GITHUB_SHA")
    if revision:
        return revision

    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    revision = result.stdout.strip()
    return revision or None


def _pair_specs(pair: str | None):
    if pair is None:
        return None
    lower_id, higher_id = pair.split("-")
    lower = next(spec for spec in AI_LEVELS if spec.level.value == lower_id)
    higher = next(spec for spec in AI_LEVELS if spec.level.value == higher_id)
    return lower, higher

def _move_label(move: Move | None) -> str:
    if move is None:
        return "-"
    if move.is_pass:
        return "pass"
    return f"{move.src}->{move.dst}"


def run_search_benchmark() -> list[dict[str, object]]:
    fixtures = (_initial_fixture(), _capture_fixture(), _check_fixture(), _endgame_fixture())

    print("AI level search benchmark")
    print("This measures search complexity, not playing strength.")
    print()
    print("level,name,fixture,depth,nodes,score_cp,best_move,elapsed_ms")

    rows: list[dict[str, object]] = []
    for spec in AI_LEVELS:
        engine = NegamaxEngine(spec.config)
        for fixture in fixtures:
            started = perf_counter()
            analysis = engine.analyze(fixture.state)
            elapsed_ms = (perf_counter() - started) * 1000.0
            row = {
                "level": spec.level.value,
                "name": spec.name,
                "fixture": fixture.name,
                "depth": analysis.depth,
                "nodes": analysis.nodes,
                "score_cp": analysis.score_cp,
                "best_move": _move_label(analysis.best_move),
                "elapsed_ms": round(elapsed_ms, 2),
            }
            rows.append(row)
            print(
                f"{spec.level.value},{spec.name},{fixture.name},"
                f"{analysis.depth},{analysis.nodes},{analysis.score_cp},"
                f"{_move_label(analysis.best_move)},{elapsed_ms:.2f}"
            )
    return rows


def _fixtures_for_mode(fixture_mode: str, setup: str) -> tuple[Fixture, ...]:
    if fixture_mode == "initial":
        return (Fixture("initial", GameState.initial(setup)),)
    if fixture_mode == "capture":
        return (_capture_fixture(),)
    if fixture_mode == "check":
        return (_check_fixture(),)
    if fixture_mode == "endgame":
        return (_endgame_fixture(),)
    if fixture_mode == "tactical":
        return (_capture_fixture(), _check_fixture(), _endgame_fixture())
    raise ValueError(f"unsupported fixture mode: {fixture_mode}")


def _play_fixture_game(
    lower_engine: NegamaxEngine,
    higher_engine: NegamaxEngine,
    fixture: Fixture,
    *,
    lower_starts_as_cho: bool,
    max_plies: int,
) -> tuple[GameStatus, int]:
    match = Match(state=fixture.state, setup="classic", rules=RuleSet())
    for _ in range(max_plies):
        if match.status is not GameStatus.PLAYING:
            break
        lower_turn = (match.state.turn is Side.CHO) == lower_starts_as_cho
        engine = lower_engine if lower_turn else higher_engine
        proposed_move = engine.choose_move(match.state)
        move = validate_engine_move(engine, match.state, proposed_move)
        match = match.play(move)
    return match.status, len(match.state.history)


def run_adjacent_tournaments(
    games: int,
    max_plies: int,
    pair: str | None = None,
    *,
    seed: int = 20260930,
    setup: str = "classic",
    fixture_mode: str = "initial",
    random_ties: bool = True,
) -> list[dict[str, object]]:
    print()
    print(f"Adjacent-level self-play benchmark: {games} games, {max_plies} plies cap, fixture={fixture_mode}")
    print("Results are exploratory strength evidence, not a calibrated rating.")
    print("lower_level,higher_level,lower_score,higher_score,lower_wins,higher_wins,draws,completed,unfinished")

    rows: list[dict[str, object]] = []
    for lower, higher in zip(AI_LEVELS, AI_LEVELS[1:]):
        pair_id = f"{lower.level.value}-{higher.level.value}"
        if pair is not None and pair_id != pair:
            continue
        lower_engine = NegamaxEngine(
            replace(
                lower.config,
                random_ties=random_ties,
                seed=seed + int(lower.level.value),
            )
        )
        higher_engine = NegamaxEngine(
            replace(
                higher.config,
                random_ties=random_ties,
                seed=seed + int(higher.level.value),
            )
        )
        fixtures = _fixtures_for_mode(fixture_mode, setup)
        lower_wins = higher_wins = draws = unfinished = 0
        game_results = []
        for index in range(games):
            fixture = fixtures[index % len(fixtures)]
            lower_starts_as_cho = index % 2 == 0
            status, plies = _play_fixture_game(
                lower_engine,
                higher_engine,
                fixture,
                lower_starts_as_cho=lower_starts_as_cho,
                max_plies=max_plies,
            )
            if status is GameStatus.PLAYING:
                unfinished += 1
                outcome_for_lower = None
            elif status is GameStatus.CHO_WIN:
                outcome_for_lower = 1 if lower_starts_as_cho else -1
                if outcome_for_lower == 1:
                    lower_wins += 1
                else:
                    higher_wins += 1
            elif status is GameStatus.HAN_WIN:
                outcome_for_lower = -1 if lower_starts_as_cho else 1
                if outcome_for_lower == 1:
                    lower_wins += 1
                else:
                    higher_wins += 1
            else:
                outcome_for_lower = 0
                draws += 1
            game_results.append(
                {
                    "game": index + 1,
                    "fixture": fixture.name,
                    "status": status.value,
                    "outcome_for_lower": outcome_for_lower,
                    "plies": plies,
                }
            )

        completed = games - unfinished
        row = {
            "lower_level": lower.level.value,
            "lower_name": lower.name,
            "higher_level": higher.level.value,
            "higher_name": higher.name,
            "games": games,
            "max_plies": max_plies,
            "fixture_mode": fixture_mode,
            "lower_score": lower_wins + draws * 0.5,
            "higher_score": higher_wins + draws * 0.5,
            "lower_wins": lower_wins,
            "higher_wins": higher_wins,
            "draws": draws,
            "completed": completed,
            "unfinished": unfinished,
            "game_results": game_results,
        }
        rows.append(row)
        print(
            f"{lower.level.value},{higher.level.value},"
            f"{lower_wins + draws * 0.5},{higher_wins + draws * 0.5},"
            f"{lower_wins},{higher_wins},{draws},"
            f"{completed},{unfinished}"
        )
    return rows



def validate_benchmark_args(
    tournament_games: int,
    max_plies: int,
    pair: str | None = None,
    setup: str = "classic",
    fixture_mode: str = "initial",
) -> None:
    if tournament_games < 0:
        raise ValueError("tournament_games must be non-negative")
    if tournament_games == 1 or tournament_games % 2:
        raise ValueError("tournament_games must be 0 or an even integer of at least 2")
    if max_plies < 1:
        raise ValueError("max_plies must be at least 1")
    if pair is not None and pair not in {"1-2", "2-3", "3-4", "4-5", "5-6"}:
        raise ValueError("pair must be one of 1-2, 2-3, 3-4, 4-5, 5-6")
    if setup not in {"classic", "left", "right", "both"}:
        raise ValueError("setup must be one of classic, left, right, both")
    if fixture_mode not in {"initial", "capture", "check", "endgame", "tactical"}:
        raise ValueError("fixture_mode must be one of initial, capture, check, endgame, tactical")


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark configured Janggi AI levels.")
    parser.add_argument(
        "--tournament-games",
        type=int,
        default=0,
        help="Also run adjacent-level self-play games.",
    )
    parser.add_argument(
        "--max-plies",
        type=int,
        default=128,
        help="Maximum plies per tournament game.",
    )
    parser.add_argument(
        "--pair",
        choices=("1-2", "2-3", "3-4", "4-5", "5-6"),
        default=None,
        help="Run one adjacent-level pair only; useful for bounded repeated calibration runs.",
    )
    parser.add_argument(
        "--skip-search-benchmark",
        action="store_true",
        help="Skip deterministic fixture search benchmarking and run only the tournament portion.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260930,
        help="Master seed for reproducible calibration tie-breaking.",
    )
    parser.add_argument(
        "--setup",
        choices=("classic", "left", "right", "both"),
        default="classic",
        help="Starting arrangement used by the initial fixture.",
    )
    parser.add_argument(
        "--fixture",
        choices=("initial", "capture", "check", "endgame", "tactical"),
        default="initial",
        help="Calibration starting position(s). Tactical cycles capture/check/endgame.",
    )
    parser.add_argument(
        "--deterministic-ties",
        action="store_true",
        help="Disable benchmark-only random tie-breaking. The default uses fixed-seed tie-breaking for game diversity.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON evidence output path.",
    )
    args = parser.parse_args()

    try:
        validate_benchmark_args(args.tournament_games, args.max_plies, args.pair, args.setup, args.fixture)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    search_rows = run_search_benchmark() if not args.skip_search_benchmark else []
    tournament_rows = (
        run_adjacent_tournaments(
            args.tournament_games,
            args.max_plies,
            args.pair,
            seed=args.seed,
            setup=args.setup,
            fixture_mode=args.fixture,
            random_ties=not args.deterministic_ties,
        )
        if args.tournament_games
        else []
    )
    if args.output is not None:
        pair_specs = _pair_specs(args.pair)
        payload = {
            "experiment": {
                "name": "adjacent AI level strength benchmark",
                "method": "head-to-head with alternating colors and optional fixture starts",
                "games_per_adjacent_pair": args.tournament_games,
                "max_plies": args.max_plies,
                "pair": args.pair,
                "setup": args.setup,
                "fixture": args.fixture,
                "seed": args.seed,
                "random_ties": not args.deterministic_ties,
                "interpretation": "exploratory evidence only; not calibrated player or model rating",
                "seeded_experiment": True,
                "runtime_reproducibility": "wall_clock_sensitive_for_time_bounded_levels",
                "benchmark_only_random_ties": True,
                "search_benchmark_included": not args.skip_search_benchmark,
                "engine_version": NegamaxEngine().info.version,
                "source_revision": _source_revision(),
                "calibration_protocol_version": str(CALIBRATION_PROTOCOL_VERSION),
                "ai_level_config_fingerprint": (
                    ai_level_configuration_fingerprint(*pair_specs)
                    if pair_specs is not None
                    else None
                ),
            },
            "pairs": tournament_rows,
            "search_fixtures": search_rows,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
