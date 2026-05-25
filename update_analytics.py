import re

with open('app/templates/analytics_studio.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Remove inline onclick handlers for chart buttons
text = re.sub(r'onclick=[\"\']setActiveChart\([^)]+\)[\"\']', '', text)

with open('app/templates/analytics_studio.html', 'w', encoding='utf-8') as f:
    f.write(text)

with open('app/static/js/analytics.js', 'r', encoding='utf-8') as f:
    js = f.read()

append_js = '''
    // Chart type button listeners
    document.querySelectorAll('.chart-type-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            if (window.setActiveChart) {
                let type = e.currentTarget.dataset.type;
                if (!type) {
                    type = e.currentTarget.innerText.trim().toLowerCase();
                }
                window.setActiveChart(type);
            }
        });
    });
'''

js = js.replace('if (window.initSelects) window.initSelects();\n});', append_js + '    if (window.initSelects) window.initSelects();\n});')

with open('app/static/js/analytics.js', 'w', encoding='utf-8') as f:
    f.write(js)

print('Analytics listeners updated successfully')
