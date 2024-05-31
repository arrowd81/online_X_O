import random
from typing import Annotated

from fastapi import FastAPI, WebSocket, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect

import auth
import models
from config import engine
from utils import check_winner
from exceptions import UserAlreadyExistsException

models.base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(auth.router)

app.mount("/login", StaticFiles(directory="static/login", html=True), name="static")
app.mount("/game", StaticFiles(directory="static/game", html=True), name="static")
user_dependency = Annotated[models.Player, Depends(auth.get_current_user)]
ws_user_dependency = Annotated[models.Player, Depends(auth.get_websocket_user)]

pending_lobby: models.GameLobby | None = None
running_games: list[models.GameLobby] = []


@app.get("/")
async def home():
    return RedirectResponse("/static/index.html")


@app.get("/new_game")
async def new_game(player: user_dependency):
    if player is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    global pending_lobby
    if not pending_lobby:
        pending_lobby = models.GameLobby()
        await pending_lobby.add_player(player,
                                       position=random.choice((models.PlayerType.first, models.PlayerType.second)))
        return pending_lobby.game_status_json()
    else:
        try:
            await pending_lobby.add_player(player)
        except UserAlreadyExistsException:
            status = pending_lobby.game_status_json()
            return status
        status = pending_lobby.game_status_json()
        running_games.append(pending_lobby)
        pending_lobby = None
        return status


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, player: ws_user_dependency, room_id: int):
    async def move(move_data):
        index = move_data["index"]
        if game_lobby.game_state.board[index] is None and game_lobby.game_state.winner is None:
            if game_lobby.game_state.validate_move(index, player):
                game_lobby.game_state.board[index] = game_lobby.game_state.current_player
                winner = check_winner(game_lobby.game_state.board)
                if winner:
                    game_lobby.game_state.winner = winner if winner != "Draw" else None
                    game_lobby.game_state.draw = winner == "Draw"
                else:
                    game_lobby.game_state.current_player = "O" if game_lobby.game_state.current_player == "X" \
                        else "X"
                await game_lobby.broadcast_game_state()

    global running_games
    for game_lobby in running_games:
        if game_lobby.room_id == room_id:
            if player not in game_lobby.players.values():
                raise HTTPException(status_code=403, detail="You are Not authorized to play in this board")
            break
    else:
        raise HTTPException(status_code=404, detail="board Not found")

    await game_lobby.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data['req'] == 'move':
                await move(data)
            if data['req'] == 'game_state':
                await game_lobby.send_game_state(websocket)
    except WebSocketDisconnect:
        game_lobby.disconnect(websocket)
