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
        .then(response => {
            if (response.status === 200) {
                response.json().then(data => {
                    localStorage.setItem('authkey', data["access_token"])
                    localStorage.setItem('username', formData.get('username'))
                    window.location.href = `http://${window.location.host}/lobby/`
                })
            } else if (response.status === 401) {
                alert('نام کاربری یا رمز عبور اشتباه است!')
            } else {
                alert('خطایی رخ داده است');
                response.json().then(data => console.error(data))
            }
        }).catch(error => {
        alert('خطایی رخ داده است: ' + error);
    });
});
