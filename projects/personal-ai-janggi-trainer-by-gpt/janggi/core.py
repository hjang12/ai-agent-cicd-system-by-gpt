from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional

BOARD_WIDTH = 9
BOARD_HEIGHT = 10
BOARD_SIZE = BOARD_WIDTH * BOARD_HEIGHT
Position = tuple[int, int]


class Side(Enum):
    CHO = "cho"
    HAN = "han"

    @property
    def forward(self) -> int:
        # Coordinates use y=0 at the top of the board. Cho is the top side.
        return 1 if self is Side.CHO else -1

    @property
    def opponent(self) -> "Side":
        return Side.HAN if self is Side.CHO else Side.CHO


class PieceType(Enum):
    GENERAL = "general"
    GUARD = "guard"
    ELEPHANT = "elephant"
    HORSE = "horse"
    CHARIOT = "chariot"
    CANNON = "cannon"
    SOLDIER = "soldier"


@dataclass(frozen=True)
class Piece:
    side: Side
    kind: PieceType


@dataclass(frozen=True)
class Move:
    src: Optional[Position]
    dst: Optional[Position]
    is_pass: bool = False

    @classmethod
    def pass_move(cls) -> "Move":
        return cls(None, None, True)


@dataclass(frozen=True)
class GameState:
    board: tuple[Optional[Piece], ...]
    turn: Side = Side.CHO
    history: tuple[Move, ...] = ()

    def __post_init__(self) -> None:
        if len(self.board) != BOARD_SIZE:
            raise ValueError(f"board must contain {BOARD_SIZE} points")

    @classmethod
    def empty(cls, turn: Side = Side.CHO) -> "GameState":
        return cls((None,) * BOARD_SIZE, turn)

    @classmethod
    def initial(cls, setup: str = "classic") -> "GameState":
        if setup not in {"classic", "left", "right", "both"}:
            raise ValueError("setup must be classic, left, right, or both")
        board: list[Optional[Piece]] = [None] * BOARD_SIZE

        def put(x: int, y: int, side: Side, kind: PieceType) -> None:
            board[index((x, y))] = Piece(side, kind)

        # y=0 is Cho's back rank; y=9 is Han's back rank.
        for x, kind in enumerate(_back_rank(setup)):
            if kind is not None:
                put(x, 0, Side.CHO, kind)
                put(x, 9, Side.HAN, kind)

        for x in (3, 5):
            put(x, 0, Side.CHO, PieceType.GUARD)
            put(x, 9, Side.HAN, PieceType.GUARD)
        # The General starts at the center point of the 3x3 palace,
        # one rank forward from the back rank.
        put(4, 1, Side.CHO, PieceType.GENERAL)
        put(4, 8, Side.HAN, PieceType.GENERAL)

        for x in (1, 7):
            put(x, 2, Side.CHO, PieceType.CANNON)
            put(x, 7, Side.HAN, PieceType.CANNON)
        for x in (0, 2, 4, 6, 8):
            put(x, 3, Side.CHO, PieceType.SOLDIER)
            put(x, 6, Side.HAN, PieceType.SOLDIER)
        return cls(tuple(board), Side.CHO)

    def piece_at(self, pos: Position) -> Optional[Piece]:
        return self.board[index(pos)]

    def _piece_at_unchecked(self, pos: Position) -> Optional[Piece]:
        x, y = pos
        return self.board[y * BOARD_WIDTH + x]

    def find_general(self, side: Side) -> Optional[Position]:
        target = Piece(side, PieceType.GENERAL)
        for pos in all_positions():
            if self._piece_at_unchecked(pos) == target:
                return pos
        return None

    def is_in_check(self, side: Optional[Side] = None) -> bool:
        side = side or self.turn
        general = self.find_general(side)
        if general is None:
            return True
        for src in all_positions():
            piece = self.piece_at(src)
            if piece is None or piece.side is side or piece.kind is PieceType.GENERAL:
                continue
            if general in _attacks(self, src):
                return True
        return False

    def is_bikjang(self) -> bool:
        cho = self.find_general(Side.CHO)
        han = self.find_general(Side.HAN)
        if cho is None or han is None or cho[0] != han[0]:
            return False
        x = cho[0]
        low, high = sorted((cho[1], han[1]))
        return all(self.piece_at((x, y)) is None for y in range(low + 1, high))

    def pseudo_moves(self, src: Position) -> tuple[Move, ...]:
        _validate_position(src)
        piece = self._piece_at_unchecked(src)
        if piece is None or piece.side is not self.turn:
            return ()
        return tuple(
            Move(src, dst)
            for dst in sorted(_piece_destinations(self, src, piece))
            if (target := self.piece_at(dst)) is None or target.side is not piece.side
        )

    def legal_moves(self, include_pass: bool = True) -> tuple[Move, ...]:
        moves: list[Move] = []
        for src in all_positions():
            piece = self.piece_at(src)
            if piece is None or piece.side is not self.turn:
                continue
            for move in self.pseudo_moves(src):
                target = self._piece_at_unchecked(move.dst) if move.dst is not None else None
                if target is not None and target.kind is PieceType.GENERAL:
                    continue
                candidate = self._apply_unchecked(move)
                if not candidate.is_in_check(self.turn):
                    moves.append(move)
        if include_pass and not self.is_in_check(self.turn):
            moves.append(Move.pass_move())
        return tuple(moves)

    def is_legal(self, move: Move) -> bool:
        return move in self.legal_moves()

    def apply(self, move: Move) -> "GameState":
        if move.is_pass:
            if self.is_in_check(self.turn):
                raise ValueError("pass is not legal while in check")
            return self._apply_unchecked(move)
        if move.src is None or move.dst is None:
            raise ValueError("non-pass moves require src and dst")
        if move not in self.pseudo_moves(move.src):
            raise ValueError("illegal piece movement")
        _validate_position(move.dst)
        target = self._piece_at_unchecked(move.dst)
        if target is not None and target.kind is PieceType.GENERAL:
            raise ValueError("capturing a general is not a legal Janggi move")
        candidate = self._apply_unchecked(move)
        if candidate.is_in_check(self.turn):
            raise ValueError("move leaves own general in check")
        return candidate

    def _apply_unchecked(self, move: Move) -> "GameState":
        if move.is_pass:
            return GameState(self.board, self.turn.opponent, self.history + (move,))
        if move.src is None or move.dst is None:
            raise ValueError("non-pass moves require src and dst")
        piece = self._piece_at_unchecked(move.src)
        if piece is None:
            raise ValueError("source square is empty")
        board = list(self.board)
        board[index(move.src)] = None
        board[index(move.dst)] = piece
        return GameState(tuple(board), self.turn.opponent, self.history + (move,))

    def position_key(self) -> tuple[object, ...]:
        return self.turn, tuple(None if p is None else (p.side, p.kind) for p in self.board)


def index(pos: Position) -> int:
    _validate_position(pos)
    x, y = pos
    return y * BOARD_WIDTH + x


def position(idx: int) -> Position:
    if not 0 <= idx < BOARD_SIZE:
        raise ValueError("index out of bounds")
    return idx % BOARD_WIDTH, idx // BOARD_WIDTH


def all_positions() -> Iterable[Position]:
    for y in range(BOARD_HEIGHT):
        for x in range(BOARD_WIDTH):
            yield x, y


def palace_for(side: Side) -> set[Position]:
    ys = (0, 1, 2) if side is Side.CHO else (7, 8, 9)
    return {(x, y) for x in range(3, 6) for y in ys}


def _validate_position(pos: Position) -> None:
    if len(pos) != 2 or not (0 <= pos[0] < BOARD_WIDTH and 0 <= pos[1] < BOARD_HEIGHT):
        raise ValueError(f"invalid board position: {pos}")


def _back_rank(setup: str) -> tuple[Optional[PieceType], ...]:
    variants = {
        "classic": (PieceType.CHARIOT, PieceType.ELEPHANT, PieceType.HORSE, None,
                    None, None, PieceType.HORSE, PieceType.ELEPHANT, PieceType.CHARIOT),
        "left": (PieceType.CHARIOT, PieceType.HORSE, PieceType.ELEPHANT, None,
                 None, None, PieceType.HORSE, PieceType.ELEPHANT, PieceType.CHARIOT),
        "right": (PieceType.CHARIOT, PieceType.ELEPHANT, PieceType.HORSE, None,
                  None, None, PieceType.ELEPHANT, PieceType.HORSE, PieceType.CHARIOT),
        "both": (PieceType.CHARIOT, PieceType.HORSE, PieceType.ELEPHANT, None,
                 None, None, PieceType.ELEPHANT, PieceType.HORSE, PieceType.CHARIOT),
    }
    return variants[setup]


def _on_palace_diagonal(pos: Position, side: Side) -> bool:
    x, y = pos
    if pos not in palace_for(side):
        return False
    local_x = x - 3
    local_y = y if side is Side.CHO else y - 7
    return local_x == local_y or local_x + local_y == 2


def _king_like_destinations(src: Position, piece: Piece) -> set[Position]:
    x, y = src
    out: set[Position] = set()
    palace = palace_for(piece.side)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        dst = x + dx, y + dy
        if dst in palace:
            out.add(dst)
    if _on_palace_diagonal(src, piece.side):
        for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            dst = x + dx, y + dy
            if dst in palace and _on_palace_diagonal(dst, piece.side):
                out.add(dst)
    return out


def _piece_destinations(state: GameState, src: Position, piece: Piece) -> set[Position]:
    if piece.kind in {PieceType.GENERAL, PieceType.GUARD}:
        return _king_like_destinations(src, piece)
    if piece.kind is PieceType.CHARIOT:
        return _chariot_destinations(state, src, piece)
    if piece.kind is PieceType.CANNON:
        return _cannon_destinations(state, src, piece)
    if piece.kind is PieceType.HORSE:
        return _horse_destinations(state, src)
    if piece.kind is PieceType.ELEPHANT:
        return _elephant_destinations(state, src)
    if piece.kind is PieceType.SOLDIER:
        return _soldier_destinations(state, src, piece)
    raise AssertionError(piece.kind)


def _ray(state: GameState, src: Position, direction: tuple[int, int], side: Side) -> set[Position]:
    out: set[Position] = set()
    x, y = src
    dx, dy = direction
    nx, ny = x + dx, y + dy
    while 0 <= nx < BOARD_WIDTH and 0 <= ny < BOARD_HEIGHT:
        dst = nx, ny
        target = state._piece_at_unchecked(dst)
        if target is None:
            out.add(dst)
        else:
            if target.side is not side:
                out.add(dst)
            break
        nx += dx
        ny += dy
    return out


def _chariot_destinations(state: GameState, src: Position, piece: Piece) -> set[Position]:
    out: set[Position] = set()
    for direction in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        out.update(_ray(state, src, direction, piece.side))
    if _on_palace_diagonal(src, piece.side):
        palace = palace_for(piece.side)
        for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            nx, ny = src[0] + dx, src[1] + dy
            while (nx, ny) in palace:
                target = state.piece_at((nx, ny))
                if target is None:
                    out.add((nx, ny))
                else:
                    if target.side is not piece.side:
                        out.add((nx, ny))
                    break
                nx += dx
                ny += dy
    return out


def _horse_destinations(state: GameState, src: Position) -> set[Position]:
    x, y = src
    out: set[Position] = set()
    for dx, dy in ((2, 1), (2, -1), (-2, 1), (-2, -1),
                   (1, 2), (1, -2), (-1, 2), (-1, -2)):
        block = (x + (1 if dx > 0 else -1), y) if abs(dx) > abs(dy) else (x, y + (1 if dy > 0 else -1))
        if not (0 <= block[0] < BOARD_WIDTH and 0 <= block[1] < BOARD_HEIGHT):
            continue
        if state.piece_at(block) is not None:
            continue
        dst = x + dx, y + dy
        if 0 <= dst[0] < BOARD_WIDTH and 0 <= dst[1] < BOARD_HEIGHT:
            out.add(dst)
    return out


def _elephant_destinations(state: GameState, src: Position) -> set[Position]:
    x, y = src
    out: set[Position] = set()
    for dx, dy in ((3, 2), (3, -2), (-3, 2), (-3, -2),
                   (2, 3), (2, -3), (-2, 3), (-2, -3)):
        sx = 1 if dx > 0 else -1
        sy = 1 if dy > 0 else -1
        if abs(dx) > abs(dy):
            first = x + sx, y
            second = x + 2 * sx, y + sy
        else:
            first = x, y + sy
            second = x + sx, y + 2 * sy
        dst = x + dx, y + dy
        if not (0 <= dst[0] < BOARD_WIDTH and 0 <= dst[1] < BOARD_HEIGHT):
            continue
        if state.piece_at(first) is not None or state.piece_at(second) is not None:
            continue
        out.add(dst)
    return out


def _cannon_destinations(state: GameState, src: Position, piece: Piece) -> set[Position]:
    out: set[Position] = set()
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = src[0] + dx, src[1] + dy
        screen_found = False
        while 0 <= nx < BOARD_WIDTH and 0 <= ny < BOARD_HEIGHT:
            target = state.piece_at((nx, ny))
            if not screen_found:
                if target is not None:
                    if target.kind is PieceType.CANNON:
                        break
                    screen_found = True
            elif target is None:
                out.add((nx, ny))
            else:
                if target.kind is not PieceType.CANNON and target.side is not piece.side:
                    out.add((nx, ny))
                break
            nx += dx
            ny += dy

    if _on_palace_diagonal(src, piece.side):
        palace = palace_for(piece.side)
        for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            nx, ny = src[0] + dx, src[1] + dy
            screen_found = False
            while (nx, ny) in palace:
                target = state.piece_at((nx, ny))
                if not screen_found:
                    if target is not None:
                        if target.kind is PieceType.CANNON:
                            break
                        screen_found = True
                elif target is None:
                    out.add((nx, ny))
                else:
                    if target.kind is not PieceType.CANNON and target.side is not piece.side:
                        out.add((nx, ny))
                    break
                nx += dx
                ny += dy
    return out


def _soldier_destinations(state: GameState, src: Position, piece: Piece) -> set[Position]:
    x, y = src
    out: set[Position] = set()
    forward = x, y + piece.side.forward
    if 0 <= forward[1] < BOARD_HEIGHT:
        out.add(forward)
    for dx in (-1, 1):
        dst = x + dx, y
        if 0 <= dst[0] < BOARD_WIDTH:
            out.add(dst)
    for dx in (-1, 1):
        dst = x + dx, y + piece.side.forward
        if 0 <= dst[0] < BOARD_WIDTH and 0 <= dst[1] < BOARD_HEIGHT and _on_palace_diagonal(dst, piece.side.opponent):
            out.add(dst)
    return out


def _attacks(state: GameState, src: Position) -> set[Position]:
    piece = state.piece_at(src)
    if piece is None:
        return set()
    return _piece_destinations(state, src, piece)
