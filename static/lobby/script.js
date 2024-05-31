function startGame() {
    document.getElementById('waiting').style.display = 'block';
    token = localStorage.getItem('authkey')
    console.log(token);
    if (token) {
        fetch(`http://${window.location.host}/new_game`, {
            method: 'GET',
            headers: {
                'Authorization': 'Bearer ' + token
            }
        }).then(response => {
            return response.json();
        }).then(data => {
            if (data["status"] === "Waiting For Opponent" || data["status"] === "Game Started") {
                window.location.href = `http://${window.location.host}/game/${data["board_id"]}`
            }
        }).catch(error => {
            console.error('Error:', error)
        });
    } else {
        alert('لطفا دوباره وارد شوید.')
    }
}

function addGameToHistory() {
    var historyList = document.getElementById('history');
    var newGame = document.createElement('p');
    newGame.textContent = 'New game played';
    historyList.appendChild(newGame);
}
