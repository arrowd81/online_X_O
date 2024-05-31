document.addEventListener("DOMContentLoaded", () => {
    const board = document.querySelector("#board");
    const cells = document.querySelectorAll(".cell");
    const status = document.querySelector("#status");
    const resetButton = document.querySelector("#reset");
    let websocket;


    function connectWebSocket() {
        token = localStorage.getItem('authkey')
        if (token) {
            url_parts = window.location.href.split('/')
            roomId = url_parts[url_parts.length - 1]
            websocket = new WebSocket(`ws://${window.location.host}/ws/${roomId}?token=${token}`);

            websocket.onmessage = function (event) {
                const gameState = JSON.parse(event.data);
                updateBoard(gameState);
            };
        } else {
            alert('لطفا دوباره وارد شوید.')
        }
    }

    function updateBoard(gameState) {
        cells.forEach((cell, index) => {
            cell.textContent = gameState.board[index] || "";
        });
        if (gameState.winner) {
            status.textContent = `Winner: ${gameState.winner}`;
        } else if (gameState.draw) {
            status.textContent = "Draw!";
        } else {
            status.textContent = `Current Player: ${gameState.current_player}`;
        }
    }

    cells.forEach(cell => {
        cell.addEventListener("click", () => {
            const index = cell.dataset.index;
            const currentState = Array.from(cells).map(cell => cell.textContent);
            const currentPlayer = status.textContent.includes("X") ? "X" : "O";

            if (!currentState[index]) {
                websocket.send(JSON.stringify({index, player: currentPlayer}));
            }
        });
    });

    resetButton.addEventListener("click", () => {
        websocket.send(JSON.stringify({reset: true}));
        websocket.close();
        connectWebSocket();
    });

    connectWebSocket();
});
