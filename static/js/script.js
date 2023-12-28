async function login(event) {
    event.preventDefault();
    let username = document.getElementById('username').value;
    let password = document.getElementById('password').value;
    const response = await fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `username=${username}&password=${password}`
    });
    if (response.ok) {
        const data = await response.json();
        console.log('Login successful:', data);
        window.location.href = '/home';
    } else {
        const data = await response.json();
        showPopup(`Login failed: ${data.error}`);
    }
}

async function register(event) {
    event.preventDefault();
    let username = document.getElementById('username').value;
    let password = document.getElementById('password').value;
    const response = await fetch('/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `username=${username}&password=${password}`
    });
    if (response.ok) {
        const data = await response.json();
        console.log('Registration successful:', data);
        window.location.href = '/home';
    } else {
        showPopup('Login failed:', response.status, response.statusText, response.error);

    }
}

function showPopup(text) {
    var popup = document.getElementById("popup");
    popup.innerHTML = text;
    popup.style.visibility = 'visible';

    // After 3 seconds, remove the show class to hide the popup
    setTimeout(function(){ popup.style.visibility = "hidden"; }, 3000);
}