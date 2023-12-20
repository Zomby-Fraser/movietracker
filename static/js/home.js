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
    var url = null;
    if (document.getElementById('imdbQueryRadio').checked) {
        var title = document.getElementById('movieTitle').value;
        var year = document.getElementById('movieYear').value;
        var post_body = `title=${title}&year=${year}`;
        url = "/search_imdb";
    }
    else {
        var imdb_link = document.getElementById('imdbLink').value;
        var post_body = `url=${imdb_link}`;
        url = "/add_movie"
    }

    await addMovie(url, post_body);
}

async function addMovieFromSearch(url) {
    await addMovie('/add_movie', `url=${url}`);
}

async function addMovie(url, post_body) {
    const response = await fetch(`http://127.0.0.1:5001/${url}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: post_body
    });
    if (response.ok) {
        const data = await response.json();
        console.log('Scrape Successful:', data);
        if (data.results) {
            let searchResultsDiv = document.getElementById('imdbSearchResuls');
            searchResultsDiv.innerHTML = '';
            data.results.forEach(result => {
                // Create a new table row element
                let row = document.createElement('tr');

                // Set the innerHTML of the row
                row.innerHTML = `
                    <td><img class="imdb-img" src="${result.image}" alt="${result.title}"></td>
                    <td><p><a href='https://www.imdb.com/title/{imdb_id}'>${result.title}</a></p></td>
                    <td><p class="imdb-year">${result.year}</p></td>
                    <td><button class="imdb-add-btn" onclick="addMovieFromSearch('${result.imdb_url}')">Add Request</button></td>
                `;

                // Append the row to the table body
                searchResultsDiv.appendChild(row);
            });

            searchResultsDiv.style.display = 'inline';
        }
        else {
            req_movie_table = document.getElementById('requestedMoviesTable');
            req_movie_table.innerHTML += data.divs;
            showPopup(`Added to the request list ${data.title} (${data.year})`);
        }
    } else {
        console.error('Scrape failed:', response.status, response.statusText);
    }
}

function closeModal() {
    document.getElementById('movieRequestModal').style.display = 'none';
}

async function updateCheckedRadio() {
    radio_btns = document.querySelectorAll(".radio-btn");
    checked_radios = {}
    radio_btns.forEach(radio => {
        let id = radio.id;
        checked_radios[id] = radio.checked;
        let source_key = id.split("_").at(-1);
        updateSelectedSource(source_key, radio.checked);
    });
}
updateCheckedRadio();

async function toggleRadio(radio) {
    let id = radio.id;
    if (checked_radios[id]) {
        radio.checked = false;
    }
    else {
        radio.checked = true;
    }
    await updateCheckedRadio();
}

async function updateSelectedSource(source_key, source_selection_flag) {
    const response = await fetch(`http://127.0.0.1:5001/update_selected_source`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `source_key=${source_key}&source_selection_flag=${source_selection_flag}`
    });
    if (response.ok) {
        console.log('Update Successful:');
    }
    else {
        console.error('Update failed:', response.status, response.statusText);
    }
}

function showPopup(text) {
    var popup = document.getElementById("popup");
    popup.innerHTML = text;
    popup.style.visibility = 'visible';

    // After 3 seconds, remove the show class to hide the popup
    setTimeout(function(){ popup.style.visibility = "hidden"; }, 3000);
}

let source_movie_key = null;
function openSourceEditor(movie_key) {
    document.getElementById('addSourceModal').style.display = 'block';
    source_movie_key = movie_key;
}

async function submitSource() { 
    let source_name = document.getElementById('sourceName').value;
    let source_tracker_options = document.querySelectorAll('.add-source-radios');
    let source_size = document.getElementById('sourceSize').value;
    let source_tracker_key = null;
    source_tracker_options.forEach(tracker => {
        if (tracker.checked) {
            source_tracker_key = tracker.id.split("tracker").at(-1);
        }
    });

    if (source_tracker_key === null || source_name.length == 0 || source_size.length == 0) {
        showPopup('Please make sure a source name and size is specified and a tracker has been selected.');
        return;
    }


    const response = await fetch(`http://127.0.0.1:5001/add_source`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `movie_key=${source_movie_key}&source_name=${source_name}&source_tracker_key=${source_tracker_key}&source_size=${source_size}`
    });
    if (response.ok) {
        console.log('Update Successful:');
        window.reload();
    }
    else {
        console.error('Update failed:', response.status, response.statusText);
    }
}


