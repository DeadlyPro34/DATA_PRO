// exports.js
document.addEventListener('DOMContentLoaded', function() {
    const exportCsvBtn = document.getElementById('exportCsvBtn');
    const exportJsonBtn = document.getElementById('exportJsonBtn');
    
    if (!exportCsvBtn && !exportJsonBtn) return;
    
    const APP_DATA = window.APP_DATA || {};
    const fileId = APP_DATA.FILE_ID;
    
    if (exportCsvBtn) {
        exportCsvBtn.addEventListener('click', () => {
            if (!fileId) return alert('No file loaded');
            window.location.href = `/dataset/${fileId}/export/csv/`;
        });
    }
    
    if (exportJsonBtn) {
        exportJsonBtn.addEventListener('click', () => {
            if (!fileId) return alert('No file loaded');
            window.location.href = `/dataset/${fileId}/export/json/`;
        });
    }
});
