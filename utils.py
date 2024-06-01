import secrets
import string

from logging_config import logger
from fastapi import WebSocket


def generate_room_id(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


def check_winner(board):
    win_conditions = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
        [0, 4, 8], [2, 4, 6]  # diagonals
    ]
    for condition in win_conditions:
        a, b, c = condition
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    if all(board):
        return "Draw"
    return None


async def send_exception(websocket: WebSocket, reason):
    logger.debug(f"Exception occurred: {reason}")
    await websocket.send_json({'status': 'exception', 'reason': reason})
