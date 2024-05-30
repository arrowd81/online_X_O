import asyncio
from typing import List, Optional

from fastapi import WebSocket
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String

from config import base
from exceptions import UserAlreadyExistsException, LobbyIsFullException, PositionIsFullException
from utils import generate_room_id


class User(base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)


class Player(BaseModel):
    username: str
    user_id: int

    def __str__(self):
        return f"{self.user_id}: {self.username}"


class PlayerType:
    first = "X"
    second = "O"


class GameState(BaseModel):
    board: List[Optional[str]] = [None] * 9
    player_x: Player
    player_y: Player
    current_player: str = PlayerType.first
    winner: Optional[str] = None
    draw: bool = False

    def validate_move(self, index: int, player: Player):
        if self.board[index] is None or self.winner is None:
            if self.current_player == PlayerType.first and player.user_id == self.player_x:
                return True
            if self.current_player == PlayerType.second and player.user_id == self.player_y:
                return True
        return False


class GameLobby:
    def __init__(self):
        self.room_id: int = generate_room_id()
        self.players_websocket: list[WebSocket] = []
        self.players: dict[str, Player] = {}
        self.game_state: GameState | None = None

    async def add_player(self, player: Player, position=None):
        assert position in (PlayerType.first, PlayerType.second, None)

        if player in self.players.values():
            raise UserAlreadyExistsException(player)

        if position:
            if not self.players.get(position):
                self.players[position] = player
            else:
                raise PositionIsFullException

        else:
            if not self.players.get(PlayerType.first):
                self.players[PlayerType.first] = player
            elif not self.players.get(PlayerType.second):
                self.players[PlayerType.second] = player
            else:
                raise LobbyIsFullException

        if len(self.players) == 2:
            await self.start_game()

    def game_status_json(self):
        if self.game_state is None:
            return {"status": "waiting for opponent", "board_id": self.room_id}
        else:
            if self.game_state.winner is None:
                return {"status": "game_started",
                        "player_X": self.players[PlayerType.first].user_id,
                        "player_Y": self.players[PlayerType.second].user_id}
            else:
                return {"status": "game_finished", "winner": self.game_state.winner}

    async def start_game(self):
        self.game_state = GameState(player_x=self.players[PlayerType.first],
                                    player_y=self.players[PlayerType.second])
        data = self.game_status_json()
        await asyncio.gather(*[player.send_json(data) for player in self.players_websocket])

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.players_websocket.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.players_websocket.remove(websocket)

    async def broadcast_game_state(self):
        await asyncio.gather(*[player.send_text(self.game_state.json()) for player in self.players_websocket])

    async def send_game_state(self, websocket: WebSocket):
        await websocket.send_text(self.game_state.json())
