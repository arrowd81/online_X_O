document.getElementById('signup-form').addEventListener('submit', function (event) {
    event.preventDefault();
    const username = document.getElementById('signup-username').value;
    const password = document.getElementById('signup-password').value;

    fetch('/auth/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            "username": username,
            "password": password
        })
    })
        .then(response => response.json())
        .then(data => {
            alert('ثبت‌نام موفقیت‌آمیز بود: ' + JSON.stringify(data));
        })
        .catch(error => {
            alert('خطایی رخ داده است: ' + error);
        });
});

document.getElementById('login-form').addEventListener('submit', function (event) {
    event.preventDefault();
    const formData = new FormData(event.target);

    fetch('/auth/token', {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
        },
        body: new URLSearchParams(formData)
    })
        .then(response => response.json())
        .then(data => {
            localStorage.setItem('authkey', data["access_token"])
            localStorage.setItem('username', formData.get('username'))
            window.location.href = `http://${window.location.host}/static/game/index.html`
        })
        .catch(error => {
            alert('خطایی رخ داده است: ' + error);
        });
});
