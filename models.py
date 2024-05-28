import asyncio
from typing import List, Optional

from fastapi import WebSocket
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String

from config import base
from utils import generate_room_id


class User(base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)


class Player(BaseModel):
    username: str
    user_id: int


class GameState(BaseModel):
    room_id: int = generate_room_id()
    board: List[Optional[str]] = [None] * 9
    player_x: Player
    player_y: Player
    current_player: str = "X"
    winner: Optional[str] = None
    draw: bool = False

    def validate_move(self, index: int, player: Player):
        if self.board[index] is None or self.winner is None:
            if self.current_player == "X" and player.user_id == self.player_x:
                return True
            if self.current_player == "O" and player.user_id == self.player_y:
                return True
        return False


class GameLobby:
    def __init__(self, game_state: GameState):
        self.players: list[WebSocket] = []
        self.game_state = game_state

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.players.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.players.remove(websocket)

    async def broadcast_game_state(self):
        await asyncio.gather(*[player.send_text(self.game_state.json()) for player in self.players])

    async def broadcast(self, message: str):
        await asyncio.gather(*[player.send_text(message) for player in self.players])
