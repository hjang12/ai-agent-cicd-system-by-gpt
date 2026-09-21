from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Optional

from .core import GameState, Move, Piece, PieceType, Position, Side


VALID_SETUPS = {"classic", "left", "right", "both"}


@dataclass(frozen=True)
class GameRecord:
    setup: str = "classic"
    moves: tuple[Move, ...] = ()
    result: Optional[str] = None
    source: str = "unknown"

    def replay(self) -> GameState:
        return _replay_moves(self.setup, self.moves)

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": "janggi-record-v1",
            "setup": self.setup,
            "source": self.source,
            "result": self.result,
            "moves": [_move_to_dict(move) for move in self.moves],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameRecord":
        if not isinstance(data, dict):
            raise ValueError("game record must be an object")
        if data.get("format") != "janggi-record-v1":
            raise ValueError("unsupported game record format")
        raw_moves = data.get("moves", [])
        if not isinstance(raw_moves, list):
            raise ValueError("moves must be a list")
        moves = tuple(_move_from_dict(item) for item in raw_moves)
        setup = data.get("setup", "classic")
        source = data.get("source", "unknown")
        result = data.get("result")
        if not isinstance(setup, str) or setup not in VALID_SETUPS:
            raise ValueError("invalid setup")
        if result is not None and not isinstance(result, str):
            raise ValueError("result must be a string or null")
        if not isinstance(source, str):
            raise ValueError("source must be a string")
        return cls(setup=setup, moves=moves, result=result, source=source)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "GameRecord":
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("game record JSON must contain an object")
        return cls.from_dict(data)


def state_to_dict(state: GameState, *, setup: Optional[str] = None) -> dict[str, Any]:
    if setup is not None:
        if not isinstance(setup, str) or setup not in VALID_SETUPS:
            raise ValueError("invalid setup")
    data: dict[str, Any] = {
        "format": "janggi-state-v1",
        "turn": state.turn.value,
        "board": [_piece_to_code(piece) for piece in state.board],
        "history": [_move_to_dict(move) for move in state.history],
    }
    if setup is not None:
        data["setup"] = setup
    return data


def state_from_dict(data: dict[str, Any], *, setup: Optional[str] = None) -> GameState:
    if not isinstance(data, dict):
        raise ValueError("game state must be an object")
    if data.get("format") != "janggi-state-v1":
        raise ValueError("unsupported game state format")

    embedded_setup = data.get("setup")
    if embedded_setup is not None and (not isinstance(embedded_setup, str) or embedded_setup not in VALID_SETUPS):
        raise ValueError("invalid setup")
    if setup is not None and (not isinstance(setup, str) or setup not in VALID_SETUPS):
        raise ValueError("invalid setup")
    if embedded_setup is not None and setup is not None and embedded_setup != setup:
        raise ValueError("embedded setup does not match requested setup")
    effective_setup = embedded_setup if embedded_setup is not None else setup

    board_data = data.get("board")
    if not isinstance(board_data, list) or len(board_data) != 90:
        raise ValueError("board must contain 90 entries")
    try:
        turn = Side(data["turn"])
    except (KeyError, ValueError) as exc:
        raise ValueError("invalid turn") from exc
    history_data = data.get("history", [])
    if not isinstance(history_data, list):
        raise ValueError("history must be a list")
    board = tuple(_code_to_piece(code) for code in board_data)
    history = tuple(_move_from_dict(item) for item in history_data)
    state = GameState(board=board, turn=turn, history=history)

    if effective_setup is not None:
        _validate_state_history(state, effective_setup)
    return state


def _validate_state_history(state: GameState, setup: str) -> None:
    if not state.history:
        if any(
            GameState.initial(setup, starting_side=side).board == state.board
            for side in (Side.HAN, Side.CHO)
        ):
            return
        raise ValueError("serialized board does not match setup")

    try:
        replayed = _replay_moves(setup, state.history)
    except ValueError as exc:
        raise ValueError("serialized history cannot be replayed from setup") from exc
    if replayed.board != state.board or replayed.turn is not state.turn:
        raise ValueError("serialized board/turn does not match history")

def _replay_moves(setup: str, moves: tuple[Move, ...]) -> GameState:
    last_error: Optional[ValueError] = None
    for starting_side in (Side.HAN, Side.CHO):
        try:
            state = GameState.initial(setup, starting_side=starting_side)
            for move in moves:
                state = state.apply(move)
            return state
        except ValueError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    raise ValueError("moves cannot be replayed from setup")


def _move_to_dict(move: Move) -> dict[str, Any]:
    return {
        "pass": move.is_pass,
        "src": _position_to_dict(move.src),
        "dst": _position_to_dict(move.dst),
    }


def _move_from_dict(data: Any) -> Move:
    if not isinstance(data, dict):
        raise ValueError("move must be an object")
    is_pass = data.get("pass", False)
    if not isinstance(is_pass, bool):
        raise ValueError("move pass flag must be boolean")
    src = _position_from_dict(data.get("src"))
    dst = _position_from_dict(data.get("dst"))
    if is_pass:
        if src is not None or dst is not None:
            raise ValueError("pass move cannot contain src/dst")
        return Move.pass_move()
    if src is None or dst is None:
        raise ValueError("normal move requires src/dst")
    return Move(src, dst)


def _position_to_dict(pos: Optional[Position]) -> Optional[list[int]]:
    return None if pos is None else [pos[0], pos[1]]


def _position_from_dict(value: Any) -> Optional[Position]:
    if value is None:
        return None
    if not isinstance(value, list) or len(value) != 2 or not all(isinstance(v, int) and not isinstance(v, bool) for v in value):
        raise ValueError("position must be [x, y] or null")
    pos = value[0], value[1]
    if not (0 <= pos[0] < 9 and 0 <= pos[1] < 10):
        raise ValueError("position out of bounds")
    return pos


def _piece_to_code(piece: Optional[Piece]) -> Optional[str]:
    if piece is None:
        return None
    return f"{piece.side.value}:{piece.kind.value}"


def _code_to_piece(code: Any) -> Optional[Piece]:
    if code is None:
        return None
    if not isinstance(code, str) or ":" not in code:
        raise ValueError("invalid piece code")
    side_name, kind_name = code.split(":", 1)
    try:
        return Piece(Side(side_name), PieceType(kind_name))
    except ValueError as exc:
        raise ValueError(f"invalid piece code: {code}") from exc
