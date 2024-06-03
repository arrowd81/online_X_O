import asyncio
from typing import List, Optional

from fastapi import WebSocket
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, ForeignKey

from config import base, Session
from exceptions import UserAlreadyExistsException, LobbyIsFullException, PositionIsFullException
from logging_config import logger
from utils import generate_room_id


class User(base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)


class Game(base):
    __tablename__ = 'game'
    id = Column(String, primary_key=True)
    player_x_id = Column(Integer, ForeignKey('user.id'))
    player_o_id = Column(Integer, ForeignKey('user.id'))
    winner = Column(String)


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
        if self.board[index] is None and self.winner is None:
            if self.current_player == PlayerType.first and player.user_id == self.player_x.user_id:
                return True
            if self.current_player == PlayerType.second and player.user_id == self.player_y.user_id:
                return True
        else:
            return False


class GameLobby:
    def __init__(self):
        self.room_id: str = generate_room_id()
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
            return {"status": "Waiting For Opponent", "board_id": self.room_id}
        else:
            data = self.game_state.model_dump(mode='json')
            data['status'] = "game_state"
            return data

    async def start_game(self):
        logger.info(f"game '{self.room_id}' started")
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
        data = self.game_state.model_dump(mode='json')
        data['status'] = "game_state"
        await asyncio.gather(*[player.send_json(data) for player in self.players_websocket])

    async def send_game_state(self, websocket: WebSocket):
        if self.game_state:
            data = self.game_state.model_dump(mode='json')
            data['status'] = "game_state"
            await websocket.send_json(data)
        else:
            await websocket.send_json(self.game_status_json())

    async def finish_game(self):
        assert (self.game_state.draw or self.game_state.winner), "game is not finished yet"
        logger.info(f"game '{self.room_id}' finished")
        await self.broadcast_game_state()
        await asyncio.gather(*[player.close() for player in self.players_websocket])
        game_in_db = Game(
            id=self.room_id,
            player_x_id=self.game_state.player_x.user_id,
            player_o_id=self.game_state.player_y.user_id,
            winner="draw" if self.game_state.draw else self.game_state.winner
        )
        with Session() as session:
            session.add(game_in_db)
            session.commit()
