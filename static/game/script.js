document.addEventListener("DOMContentLoaded", () => {
    const cells = document.querySelectorAll(".cell");
    const status = document.querySelector("#status");
    const info = document.querySelector("#info");
    const resetButton = document.querySelector("#reset");
    const waitingAnimation = document.getElementById('waiting')
    let websocket;
    let player;


    function connectWebSocket() {
        token = localStorage.getItem('authkey')
        if (token) {
            url_parts = window.location.href.split('/')
            roomId = url_parts[url_parts.length - 1]
            websocket = new WebSocket(`ws://${window.location.host}/ws/${roomId}?token=${token}`);
            websocket.onopen = function (event) {
                websocket.send(JSON.stringify({type: "game_state"}));
            }

            websocket.onmessage = function (event) {
                const data = JSON.parse(event.data);
                console.log(data)
                switch (data.status) {
                    case "game_state":
                        waitingAnimation.style.display = 'none'
                        updateBoard(data);
                        break;
                    case "Waiting For Opponent":
                        info.textContent = "Waiting For Opponent"
                        waitingAnimation.style.display = 'block';
                        break;
                    case "exception":
                        status.textContent = data.reason
                        setTimeout(() => {
                            websocket.send(JSON.stringify({type: "game_state"}));
                        }, 2000);
                        break;
                }
            };

            websocket.onerror = function (event) {
                console.error(event)
                window.location.href = `http://${window.location.host}/lobby/`
            }
        } else {
            alert('لطفا دوباره وارد شوید.')
            window.location.href = `http://${window.location.host}/lobby/`
        }
    }

    function updateBoard(gameState) {
        cells.forEach((cell, index) => {
            cell.textContent = gameState.board[index] || "";
        });
        switch (localStorage.getItem('username')) {
            case gameState.player_x.username:
                info.textContent = "you are player X"
                player = "X"
                break;
            case gameState.player_y.username:
                info.textContent = "you are player O"
                player = "O"
                break;
        }
        if (gameState.winner) {
            status.textContent = `Winner: ${gameState.winner}`;
        } else if (gameState.draw) {
            status.textContent = "Draw!";
        } else if (gameState.current_player === player) {
            status.textContent = `your turn`;
        } else {
            status.textContent = `waiting for player: ${gameState.current_player}`;
        }
    }

    cells.forEach(cell => {
        cell.addEventListener("click", () => {
            const index = cell.dataset.index;
            const currentState = Array.from(cells).map(cell => cell.textContent);

            if (!currentState[index]) {
                if (websocket.readyState === WebSocket.CLOSED) {
                    resetButton.click()
                }
                websocket.send(JSON.stringify({type: 'move', index}));
            }
        });
    });

    resetButton.addEventListener("click", () => {
        websocket.close();
        connectWebSocket();
    });

    connectWebSocket();
});
