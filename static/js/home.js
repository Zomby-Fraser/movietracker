document.getElementById('requestMovieBtn').addEventListener('click', function() {
    document.getElementById('movieRequestModal').style.display = 'block';
});

document.getElementById('imdbLinkRadio').addEventListener('change', function() {
    document.getElementById('linkField').style.display = 'block';
    document.getElementById('searchFields').style.display = 'none';
});

document.getElementById('imdbQueryRadio').addEventListener('change', function() {
    document.getElementById('linkField').style.display = 'none';
    document.getElementById('searchFields').style.display = 'block';
});

async function submitMovieRequest() {
    if (document.getElementById('requestMovieBtn').checked) {
        var title = document.getElementById('movieTitle').value;
        var year = document.getElementById('movieYear').value;
        var post_body = `title=${title}&year=${year}`;
    }
    else {
        var imdb_link = document.getElementById('imdbLink').value;
        var post_body = `url=${imdb_link}`;
    }
    

    // Logic to handle the movie request submission
    // This might involve an AJAX request to your Flask backend
    const response = await fetch('http://zombyfraser.pythonanywhere.com/add_movie', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: post_body
    });
    if (response.ok) {
        const data = await response.json();
        console.log('Scrape Successful:', data);
    } else {
        console.error('Login failed:', response.status, response.statusText);
    }

    closeModal(); // Close the modal after submission
}

function closeModal() {
    document.getElementById('movieRequestModal').style.display = 'none';
}

