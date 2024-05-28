import random
from typing import Annotated

from fastapi import FastAPI, WebSocket, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect

import auth
import models
from config import engine
from utils import check_winner

models.base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(auth.router)

app.mount("/", StaticFiles(directory="static"), name="static")
user_dependency = Annotated[models.Player, Depends(auth.get_current_user)]
ws_user_dependency = Annotated[models.Player, Depends(auth.get_websocket_user)]

pending_user = None
running_games: list[models.GameLobby] = []


@app.get("/")
async def home(user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"Hello": "World"}


@app.get("/new_game")
async def new_game(player: user_dependency):
    if player is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    global pending_user
    if not pending_user:
        pending_user = player
        return {"status": "waiting for opponent"}
    else:
        game_state = models.GameState(player_x=player, player_y=pending_user) if random.choice(
            [True, False]) else models.GameState(player_x=pending_user, player_y=player)
        global running_games
        running_games.append(models.GameLobby(game_state))


@app.websocket("/ws/{board_id}")
async def websocket_endpoint(websocket: WebSocket, player: ws_user_dependency, board_id: int):
    global running_games
    for game_lobby in running_games:
        if game_lobby.game_state.board_id == board_id:
            if (game_lobby.game_state.player_x.user_id != player.user_id and
                    game_lobby.game_state.player_y.user_id != player.user_id):
                raise HTTPException(status_code=403, detail="Not authorized to play in this board")
            break
    else:
        raise HTTPException(status_code=404, detail="board Not found")

    await game_lobby.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            index = data["index"]
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
    except WebSocketDisconnect:
        game_lobby.disconnect(websocket)
