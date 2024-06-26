import random
from typing import Annotated

from fastapi import FastAPI, WebSocket, Depends, HTTPException, WebSocketException
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import or_
from sqlalchemy.orm import aliased
from starlette.websockets import WebSocketDisconnect

import auth
import models
from config import engine
from exceptions import UserAlreadyExistsException
from logging_config import logger
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


@app.get("/history")
async def get_history(player: user_dependency, db: auth.db_dependency):
    if player is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    PlayerX = aliased(models.User, name='player_x')
    PlayerO = aliased(models.User, name='player_o')
    games_query = db.query(models.Game.id.label("game_id"),
                           PlayerX.username.label("player_x_username"),
                           PlayerO.username.label("player_o_username"),
                           models.Game.winner.label('winner')
                           ).join(PlayerX, models.Game.player_x_id == PlayerX.id) \
        .join(PlayerO, models.Game.player_o_id == PlayerO.id) \
        .filter(or_(models.Game.player_x_id == player.user_id, models.Game.player_o_id == player.user_id))
    games = games_query.all()
    return [{
        'game_id': game.game_id,
        'player_x_username': game.player_x_username,
        'player_o_username': game.player_o_username,
        'winner': game.winner
    } for game in games]


@app.get("/game/{game_id}")
async def get_game(game_id: str):
    return FileResponse("./static/game/index.html")


@app.get("/new_game")
async def new_game(player: user_dependency):
    if player is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    global running_games
    try:
        lobby = next(lobby for lobby in running_games if player in lobby.players.values())
        return lobby.room_id
    except StopIteration:
        global pending_lobby
        if not pending_lobby:
            pending_lobby = models.GameLobby()
            await pending_lobby.add_player(player,
                                           position=random.choice((models.PlayerType.first, models.PlayerType.second)))
            logger.info(f"new lobby created: {pending_lobby.room_id}")
            running_games.append(pending_lobby)
            return pending_lobby.room_id
        else:
            try:
                await pending_lobby.add_player(player)
                logger.info(f"player {player.username} added to lobby {pending_lobby.room_id}")
            except UserAlreadyExistsException:
                return pending_lobby.room_id
            status = pending_lobby.room_id
            pending_lobby = None
            return status


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, player: ws_user_dependency):
    async def move(move_data):
        index = int(move_data["index"])
        if game_lobby.game_state.board[index] is None and game_lobby.game_state.winner is None:
            if game_lobby.game_state.validate_move(index, player):
                game_lobby.game_state.board[index] = game_lobby.game_state.current_player
                winner = check_winner(game_lobby.game_state.board)
                if winner:
                    game_lobby.game_state.winner = winner if winner != "Draw" else None
                    game_lobby.game_state.draw = winner == "Draw"
                    await game_lobby.finish_game()
                    return True
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
            logger.debug(f"{data}")
            request_type = data.get("type")
            logger.debug(f"request type: {request_type}")
            if not request_type:
                await send_exception(websocket, reason=f"type not found in data: {data}")
            elif request_type == 'move':
                if game_lobby.game_state:
                    finished = await move(data)
                    if finished:
                        running_games.remove(game_lobby)
                        break
                else:
                    await send_exception(websocket, reason="game has not started yet")
            elif request_type == 'game_state':
                await game_lobby.send_game_state(websocket)
            else:
                await send_exception(websocket, reason="data['type'] not valid")
    except WebSocketDisconnect:
        game_lobby.disconnect(websocket)
