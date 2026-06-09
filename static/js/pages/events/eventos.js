document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('event-search');
    const dateFromInput = document.getElementById('date-from');
    const dateToInput = document.getElementById('date-to');
    const categoryFilter = document.getElementById('category-filter');
    const eventGrid = document.getElementById('event-grid');
    const eventCards = document.querySelectorAll('.event-card-modern');
    const noResults = document.getElementById('no-results');

    function filterEvents() {
        const searchTerm = searchInput.value.toLowerCase();
        const dateFrom = dateFromInput.value;
        const dateTo = dateToInput.value;
        const selectedCategory = categoryFilter.value;

        let visibleCount = 0;

        eventCards.forEach(card => {
            const title = card.getAttribute('data-title').toLowerCase();
            const category = card.getAttribute('data-category');
            const eventDate = card.getAttribute('data-date');

            const matchesSearch = title.includes(searchTerm);
            const matchesCategory = selectedCategory === 'todos' || category === selectedCategory;
            
            let matchesDate = true;
            if (dateFrom && eventDate < dateFrom) matchesDate = false;
            if (dateTo && eventDate > dateTo) matchesDate = false;

            if (matchesSearch && matchesCategory && matchesDate) {
                card.style.display = 'flex';
                card.classList.add('fade-in');
                visibleCount++;
            } else {
                card.style.display = 'none';
                card.classList.remove('fade-in');
            }
        });

        // Mostrar mensaje si no hay resultados
        if (visibleCount === 0) {
            noResults.classList.remove('hidden');
            eventGrid.classList.add('hidden');
        } else {
            noResults.classList.add('hidden');
            eventGrid.classList.remove('hidden');
        }
    }

    // Event listeners para tiempo real
    searchInput.addEventListener('input', filterEvents);
    dateFromInput.addEventListener('change', filterEvents);
    dateToInput.addEventListener('change', filterEvents);
    categoryFilter.addEventListener('change', filterEvents);
});
