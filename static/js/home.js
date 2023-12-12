document.getElementById('requestMovieBtn').addEventListener('click', function() {
    document.getElementById('movieRequestModal').style.display = 'block';
});

function closeModal() {
    document.getElementById('movieRequestModal').style.display = 'none';
}

function submitMovieRequest() {
    var title = document.getElementById('movieTitle').value;
    var year = document.getElementById('movieYear').value;
    var imdbLink = document.getElementById('imdbLink').value;

    // Logic to handle the movie request submission
    // This might involve an AJAX request to your Flask backend

    closeModal(); // Close the modal after submission
}