// shared.js

document.addEventListener('DOMContentLoaded', function() {
    window.APP_DATA = window.APP_DATA || {};
    
    // Shared Utilities
    window.fmtNum = function(n) {
        if (n === undefined || n === null || (typeof n === 'number' && isNaN(n))) return '—';
        const abs = Math.abs(n);
        if (abs >= 1e9) return (n/1e9).toFixed(2) + 'B';
        if (abs >= 1e6) return (n/1e6).toFixed(2) + 'M';
        if (abs >= 1e3) return (n/1e3).toFixed(2) + 'K';
        return Number.isInteger(n) ? n.toLocaleString() : parseFloat(n.toFixed(4)).toLocaleString();
    };

    window.getCsrfToken = function() {
        return document.cookie.split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1] || '';
    };

    window.showLoadingState = function(btn) {
        if (!btn) return;
        btn.dataset.originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<svg class="w-4 h-4 animate-spin inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg> Processing...';
    };

    window.restoreButtonState = function(btn) {
        if (!btn || !btn.dataset.originalHtml) return;
        btn.innerHTML = btn.dataset.originalHtml;
        btn.disabled = false;
    };
});
