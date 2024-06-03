function startGame() {
    let token = localStorage.getItem('authkey')
    if (token) {
        fetch(`http://${window.location.host}/new_game`, {
            method: 'GET',
            headers: {
                'Authorization': 'Bearer ' + token
            }
        }).then(response => {
            if (response.status === 401) {
                alert('لطفا دوباره وارد شوید.')
                window.location.href = `http://${window.location.host}/login/`
            }
            return response.json();
        }).then(data => {
            window.location.href = `http://${window.location.host}/game/${data}`
        }).catch(error => {
            console.error('Error:', error)
        });
    } else {
        alert('لطفا دوباره وارد شوید.')
    }
}

document.addEventListener("DOMContentLoaded", () => {
    let token = localStorage.getItem('authkey')
    if (token) {
        fetch(`http://${window.location.host}/history`, {
            method: 'GET',
            headers: {
                'Authorization': 'Bearer ' + token
            }
        }).then(response => {
            if (response.status === 401) {
                alert('لطفا دوباره وارد شوید.')
                window.location.href = `http://${window.location.host}/login/`
            }
            return response.json();
        }).then(data => {
            updateGameHistory(data)
        }).catch(error => {
            console.error('Error:', error)
        });
    } else {
        alert('لطفا دوباره وارد شوید.')
    }
});

function updateGameHistory(gameData) {
    const tableBody = document.querySelector('#gameTable tbody');
    const username = localStorage.getItem('username')

    gameData.forEach(game => {
        const row = document.createElement('tr');

        const cellId = document.createElement('td');
        cellId.textContent = game.game_id;
        row.appendChild(cellId);

        const cellOpponent = document.createElement('td');
        switch (username) {
            case game.player_o_username:
                cellOpponent.textContent = game.player_x_username;
                break;
            case game.player_x_username:
                cellOpponent.textContent = game.player_o_username
        }
        row.appendChild(cellOpponent);

        const cellStatus = document.createElement('td');
        switch (game.winner) {
            case "X":
                if (game.player_x_username === username) {
                    cellStatus.textContent = "Win";
                    row.classList.add('status-win');
                } else {
                    cellStatus.textContent = "Loss";
                    row.classList.add('status-loss');
                }
                break;
            case "O":
                if (game.player_o_username === username) {
                    cellStatus.textContent = "Win";
                    row.classList.add('status-win');
                } else {
                    cellStatus.textContent = "Loss";
                    row.classList.add('status-loss');
                }
                break;
            case "draw":
                cellStatus.textContent = "Draw";
                row.classList.add('status-draw');
                break;
        }
        row.appendChild(cellStatus);

        tableBody.appendChild(row);
    });
}