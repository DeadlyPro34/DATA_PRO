import re

with open('app/templates/data_explorer.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Remove inline onclick handlers for tabs
text = re.sub(r'onclick=[\"\']switchDataTab\([^)]+\)[\"\']', '', text)

with open('app/templates/data_explorer.html', 'w', encoding='utf-8') as f:
    f.write(text)

with open('app/static/js/explorer.js', 'r', encoding='utf-8') as f:
    js = f.read()

append_js = '''
    // Tab event listeners
    document.querySelectorAll('.data-tab').forEach(btn => {
        btn.addEventListener('click', (e) => {
            if (window.switchDataTab) window.switchDataTab(e.currentTarget.dataset.tab);
        });
    });
'''

js = js.replace('if (window.initSelects) window.initSelects();\n});', append_js + '    if (window.initSelects) window.initSelects();\n});')

with open('app/static/js/explorer.js', 'w', encoding='utf-8') as f:
    f.write(js)

print('Tab listeners updated successfully')
