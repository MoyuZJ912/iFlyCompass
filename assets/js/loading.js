window.addEventListener('load', function() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        setTimeout(function() {
            loadingOverlay.classList.add('hidden');
            setTimeout(function() {
                loadingOverlay.style.display = 'none';
            }, 500);
        }, 300);
    }
});