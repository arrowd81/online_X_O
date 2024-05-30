document.addEventListener("DOMContentLoaded", () => {
    const board = document.querySelector("#board");
    const cells = document.querySelectorAll(".cell");
    const status = document.querySelector("#status");
    const resetButton = document.querySelector("#reset");
    let websocket;

    async function createNewGame() {
        try {
            const response = await fetch(`http://${window.location.host}/new_game`); // Send the request
            if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
            }
            return await response.json();
        } catch (error) {
            console.error('There has been a problem with your fetch operation:', error);
        }
    }

    function connectWebSocket() {
        websocket = new WebSocket(`ws://${window.location.host}/ws`);

        websocket.onmessage = function (event) {
            const gameState = JSON.parse(event.data);
            updateBoard(gameState);
        };
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
