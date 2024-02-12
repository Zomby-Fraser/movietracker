function redirectToPage(url) {
    window.location.href = url;
}

let currentPage = 1;

function changePage(delta) {
    const newPage = currentPage + delta;
    if (newPage > 0 && newPage <= maxPage) { // Ensuring the page number is always greater than 0
        currentPage = newPage;
        updatePageInfo();
    }
}

function jumpToPage() {
    const jumpInput = document.getElementById('jumpToPageInput');
    console.log(jumpInput.value);
    const pageNumber = parseInt(jumpInput.value);
    if (!isNaN(pageNumber) && pageNumber > 0 && pageNumber < maxPage) { // Ensuring the page number is valid and greater than 0
        currentPage = pageNumber;
        updatePageInfo();
    } else {
        alert('Please enter a valid page number greater than 0.'); // Optional: Alert for invalid input
    }
}

async function updatePageInfo() {
    const pageInfo = document.getElementById('pageInfo');
    pageInfo.textContent = 'Page ' + currentPage;
    var post_body = `user_id=7&page=${currentPage}`;
    const response = await fetch('/query_collection', {
        method: 'POST',
        headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: post_body
    });
    if (response.ok) {
        const data = await response.json();
        if (data.divs) {
            let collectionTable = document.getElementById('requestedMoviesTable');
            collectionTable.innerHTML = data.divs;
        }
    }
}

async function updateSubtitleStatus(status) {
    var post_body = `user_id=7&status=${status}&movie_key=${manage_movie_key}`;
    const response = await fetch('/update_sub_status', {
        method: 'POST',
        headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: post_body
    });
    if (response.ok) {
        const data = await response.json();
        if (data.response) {
            var movie_div = document.getElementById(`movie${manage_movie_key}`);
            if (status == 'missing') {
                movie_div.style.backgroundColor = 'gold';
            }
            else {
                movie_div.style.backgroundColor = ''; 
            }
        }
    }
}

var manage_movie_key = null;

function manageMovie(movie_key) {
    document.getElementById('movieManagerModal').style.display = 'block';
    manage_movie_key = movie_key;
    let movie_div_color = document.getElementById(`movie${movie_key}`).style.backgroundColor;
    if (movie_div_color) {
        document.getElementById('missingSubtitle').checked = true;
    }
    else {
        document.getElementById('hasSubtitle').checked = true;
    }
}

function closeModal() {
    document.getElementById('movieManagerModal').style.display = 'none';
}
