// js/dark-mode.js

document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('darkModeToggle');
    const body = document.body;
    
    // Check local storage for preference
    const darkModePref = localStorage.getItem('darkMode') === 'enabled';
    
    // If enabled in local storage, apply class and update icon
    if (darkModePref) {
        body.classList.add('dark-mode');
        updateIcon(true);
    }
    
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            body.classList.toggle('dark-mode');
            const isDarkMode = body.classList.contains('dark-mode');
            
            // Save to local storage
            localStorage.setItem('darkMode', isDarkMode ? 'enabled' : 'disabled');
            
            // Update icon
            updateIcon(isDarkMode);
        });
    }

    function updateIcon(isDark) {
        if (!toggleBtn) return;
        const iconInfo = toggleBtn.querySelector('i');
        if (isDark) {
            iconInfo.classList.remove('fa-moon');
            iconInfo.classList.add('fa-sun');
        } else {
            iconInfo.classList.remove('fa-sun');
            iconInfo.classList.add('fa-moon');
        }
    }
});
