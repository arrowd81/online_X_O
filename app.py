import random
from typing import Annotated

from logging_config import logger
from fastapi import FastAPI, WebSocket, Depends, HTTPException, WebSocketException
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect

import auth
import models
from config import engine
from exceptions import UserAlreadyExistsException
from utils import check_winner, send_exception

models.base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(auth.router)
app.mount("/login", StaticFiles(directory="static/login", html=True), name="static")
app.mount("/game_resources", StaticFiles(directory="static/game", html=True), name="static")
app.mount("/lobby", StaticFiles(directory="static/lobby", html=True), name="static")
user_dependency = Annotated[models.Player, Depends(auth.get_current_user)]
ws_user_dependency = Annotated[models.Player, Depends(auth.get_websocket_user)]

pending_lobby: models.GameLobby | None = None
running_games: list[models.GameLobby] = []


@app.get("/")
async def home():
    return RedirectResponse("/login")


@app.get("/game/{game_id}")
async def get_game(game_id: str):
    return FileResponse("./static/game/index.html")


@app.get("/new_game")
async def new_game(player: user_dependency):
    if player is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    global pending_lobby
    if not pending_lobby:
        pending_lobby = models.GameLobby()
        await pending_lobby.add_player(player,
                                       position=random.choice((models.PlayerType.first, models.PlayerType.second)))
        logger.info(f"new lobby created: {pending_lobby.room_id}")
        global running_games
        running_games.append(pending_lobby)
        return pending_lobby.game_status_json()
    else:
        try:
            await pending_lobby.add_player(player)
            logger.info(f"player {player.username} added to lobby {pending_lobby.room_id}")
        except UserAlreadyExistsException:
            status = pending_lobby.game_status_json()
            return status
        status = pending_lobby.game_status_json()
        pending_lobby = None
        return status


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, player: ws_user_dependency):
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
            else:
                await send_exception(websocket, reason="Invalid move")

    global running_games
    for game_lobby in running_games:
        if game_lobby.room_id == room_id:
            if player not in game_lobby.players.values():
                logger.warning(f"player '{player}' not found in lobby '{game_lobby.room_id}'")
                raise WebSocketException(code=1008, reason="You are Not authorized to play in this board")
            break
    else:
        logger.warning(f"lobby '{room_id}' not found")
        raise WebSocketException(code=1008, reason="board Not found")

    await game_lobby.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            request_type = data.get("type")
            if not request_type:
                await send_exception(websocket, reason=f"type not found in data: {data}")
            elif request_type == 'move':
                if game_lobby.game_state:
                    await move(data)
                else:
                    await send_exception(websocket, reason="game has not started yet")
            elif request_type == 'game_state':
                await game_lobby.send_game_state(websocket)
            else:
                await send_exception(websocket, reason="data['type'] not valid")
    except WebSocketDisconnect:
        game_lobby.disconnect(websocket)
