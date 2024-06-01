function startGame() {
    token = localStorage.getItem('authkey')
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

function addGameToHistory() {
    var historyList = document.getElementById('history');
    var newGame = document.createElement('p');
    newGame.textContent = 'New game played';
    historyList.appendChild(newGame);
}
