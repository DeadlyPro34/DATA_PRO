// chat.js
document.addEventListener('DOMContentLoaded', function() {
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatMessages = document.getElementById('chatMessages');
    const APP_DATA = window.APP_DATA || {};

    if (!chatInput || !sendBtn || !chatMessages) return;

    function appendMessage(text, isUser) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `flex gap-4 p-4 rounded-xl max-w-[85%] animate-fade-in ${isUser ? 'bg-indigo-500/10 border border-indigo-500/20 text-indigo-100 self-end ml-auto' : 'bg-stone-900/50 border border-stone-800 text-stone-300'}`;
        
        let iconHtml = isUser 
            ? `<div class="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center shrink-0 shadow-lg shadow-indigo-500/30">
                <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
               </div>`
            : `<div class="w-8 h-8 rounded-full bg-violet-500 flex items-center justify-center shrink-0 shadow-lg shadow-violet-500/30">
                <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
               </div>`;

        // We sanitize and render text
        msgDiv.innerHTML = `
            ${!isUser ? iconHtml : ''}
            <div class="flex-1 text-sm leading-relaxed whitespace-pre-wrap">${text}</div>
            ${isUser ? iconHtml : ''}
        `;
        
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendQuery() {
        const query = chatInput.value.trim();
        if (!query) return;

        appendMessage(query, true);
        chatInput.value = '';
        
        if (window.showLoadingState) window.showLoadingState(sendBtn);
        
        // Add typing indicator
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typingIndicator';
        typingDiv.className = 'flex gap-4 p-4 rounded-xl max-w-[85%] bg-stone-900/50 border border-stone-800 text-stone-300 animate-fade-in';
        typingDiv.innerHTML = `
            <div class="w-8 h-8 rounded-full bg-violet-500 flex items-center justify-center shrink-0 shadow-lg shadow-violet-500/30">
                <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
            </div>
            <div class="flex-1 text-sm leading-relaxed flex items-center gap-2">
                <div class="w-1.5 h-1.5 rounded-full bg-stone-500 animate-bounce"></div>
                <div class="w-1.5 h-1.5 rounded-full bg-stone-500 animate-bounce" style="animation-delay: 0.2s"></div>
                <div class="w-1.5 h-1.5 rounded-full bg-stone-500 animate-bounce" style="animation-delay: 0.4s"></div>
            </div>
        `;
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const csrf = window.getCsrfToken ? window.getCsrfToken() : '';
            const response = await fetch(`/dataset/${APP_DATA.FILE_ID}/ai-chat/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf
                },
                body: JSON.stringify({ message: query })
            });

            const data = await response.json();
            document.getElementById('typingIndicator')?.remove();

            if (data.error) {
                appendMessage(`Error: ${data.error}`, false);
            } else {
                appendMessage(data.reply, false);
            }
        } catch (e) {
            document.getElementById('typingIndicator')?.remove();
            appendMessage(`Connection error: ${e.message}`, false);
        } finally {
            if (window.restoreButtonState) window.restoreButtonState(sendBtn);
        }
    }

    sendBtn.addEventListener('click', sendQuery);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendQuery();
    });
});
