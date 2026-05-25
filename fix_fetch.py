import sys

with open('app/templates/cleaning_lab.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_func = False
for line in lines:
    if line.startswith('async function recleanDataset() {'):
        in_func = True
        new_lines.append('''async function recleanDataset() {
    const btn = document.getElementById('recleanBtn');
    if (!btn) return;
    btn.disabled = true;
    btn.innerHTML = '<svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg> Processing...';
    
    updatePipelineVisuals();
    
    try {
        const fileId = window.APP_DATA && window.APP_DATA.FILE_ID ? window.APP_DATA.FILE_ID : '';
        const response = await fetch(`/dataset/${fileId}/reclean/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(currentOptions)
        });
        
        if (!response.ok) {
            let errorMsg = `HTTP ${response.status}`;
            try {
                const errData = await response.json();
                if (errData.error) errorMsg = errData.error;
            } catch (e) {}
            throw new Error(errorMsg);
        }
        
        const data = await response.json();
        console.log('Reclean success:', data);
        
        setTimeout(() => {
            window.location.reload();
        }, 500);
        
    } catch (e) {
        console.error('Reclean API Error:', e);
        alert('Cleaning failed: ' + e.message);
        
        btn.disabled = false;
        btn.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg> Re-Clean Dataset';
        
        const steps = document.querySelectorAll('.pipeline-step .step-dot');
        steps.forEach((s, i) => {
            if (i === 0) return;
            s.className = 'step-dot bg-stone-800 text-stone-500';
            const svg = s.querySelector('svg');
            if (svg) svg.classList.remove('animate-spin');
        });
    }
}
''')
        continue
    
    if in_func:
        if line.startswith('}'):
            in_func = False
        continue
    
    new_lines.append(line)

with open('app/templates/cleaning_lab.html', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Fixed cleaning_lab.html.')
