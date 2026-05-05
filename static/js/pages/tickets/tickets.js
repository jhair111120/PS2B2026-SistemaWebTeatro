/**
 * Mis Entradas JS
 */

document.addEventListener('DOMContentLoaded', () => {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const upcomingGrid = document.getElementById('upcoming-events');
    const pastGrid = document.getElementById('past-events');
    const modal = document.getElementById('qr-modal');
    const closeBtn = document.getElementById('close-modal');

    // Tab switching
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const tab = btn.dataset.tab;
            if (tab === 'upcoming') {
                upcomingGrid.classList.remove('hidden');
                pastGrid.classList.add('hidden');
            } else {
                upcomingGrid.classList.add('hidden');
                pastGrid.classList.remove('hidden');
            }
        });
    });

    // Modal open (using event delegation for the grids)
    document.addEventListener('click', (e) => {
        if (e.target.closest('.btn-qr')) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    });

    // Modal close
    const closeModal = () => {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    };

    closeBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });
});
