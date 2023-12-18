async function login(event) {
    event.preventDefault();
    let username = document.getElementById('username').value;
    let password = document.getElementById('password').value;
    const response = await fetch('http://127.0.0.1:5001/login', {
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
        console.error('Login failed:', response.status, response.statusText, response.error);
    }
}