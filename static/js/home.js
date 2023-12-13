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

function submitMovieRequest() {
    var title = document.getElementById('movieTitle').value;
    var year = document.getElementById('movieYear').value;
    var imdbLink = document.getElementById('imdbLink').value;

    // Logic to handle the movie request submission
    // This might involve an AJAX request to your Flask backend

    closeModal(); // Close the modal after submission
}

function closeModal() {
    document.getElementById('movieRequestModal').style.display = 'none';
}

