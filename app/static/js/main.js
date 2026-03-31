// ShiverTone - Frontend JS

const searchInput = document.getElementById('searchInput');

// Search on Enter key
searchInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') doSearch();
});

async function doSearch() {
    const query = searchInput.value.trim();
    if (!query) return;

    showLoading();

    try {
        // Fetch listings and stats in parallel
        const [listingsRes, statsRes] = await Promise.all([
            fetch(`/search?q=${encodeURIComponent(query)}`),
            fetch(`/stats?q=${encodeURIComponent(query)}`)
        ]);

        const listings = await listingsRes.json();
        const stats = await statsRes.json();

        displayStats(stats);
        displayListings(listings, query);

    } catch (err) {
        console.error(err);
        showError();
    }
}

function displayStats(stats) {
    if (!stats.count) return;

    document.getElementById('priceStats').style.display = 'grid';
    document.getElementById('statAvg').textContent = '$' + stats.avg.toLocaleString();
    document.getElementById('statMin').textContent = '$' + stats.min.toLocaleString();
    document.getElementById('statMax').textContent = '$' + stats.max.toLocaleString();
    document.getElementById('statCount').textContent = stats.count;
}

function displayListings(listings, query) {
    hideLoading();

    const summary = document.getElementById('resultsSummary');
    const resultsDiv = document.getElementById('results');

    if (listings.length === 0) {
        summary.style.display = 'none';
        document.getElementById('priceStats').style.display = 'none';
        resultsDiv.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <div class="empty-state-text">No results for "${query}"</div>
                <div class="empty-state-sub">Try a different search term</div>
            </div>
        `;
        return;
    }

    summary.style.display = 'block';
    summary.innerHTML = `Found <span>${listings.length}</span> sold listings for "<span>${query}</span>"`;

    const cards = listings.map(listing => {
        const thumb = listing.thumbnail
            ? `<img class="listing-thumb" src="${listing.thumbnail}" alt="" onerror="this.style.display='none'">`
            : `<div class="listing-thumb-placeholder">🎛️</div>`;

        const date = listing.date
            ? listing.date.substring(0, 10)
            : '';

        const url = listing.url || '#';

        return `
            <a class="listing-card" href="${url}" target="_blank">
                ${thumb}
                <div class="listing-info">
                    <div class="listing-title">${listing.title}</div>
                    <div class="listing-meta">
                        <span class="listing-platform">${listing.platform}</span>
                        <span class="listing-condition">${listing.condition}</span>
                        <span class="listing-date">${date}</span>
                    </div>
                </div>
                <div class="listing-price">$${listing.price.toLocaleString()}</div>
            </a>
        `;
    }).join('');

    resultsDiv.innerHTML = `<div class="listings">${cards}</div>`;
}

function showLoading() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').innerHTML = '';
    document.getElementById('priceStats').style.display = 'none';
    document.getElementById('resultsSummary').style.display = 'none';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

function showError() {
    hideLoading();
    document.getElementById('results').innerHTML = `
        <div class="empty-state">
            <div class="empty-state-icon">⚠️</div>
            <div class="empty-state-text">Something went wrong</div>
            <div class="empty-state-sub">Please try again</div>
        </div>
    `;
}