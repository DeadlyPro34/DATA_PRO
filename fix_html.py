import re

with open('app/templates/analytics_studio.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the Chart Type Sector
chart_type_html = '''<!-- Chart Type Selector -->
    <div class="mb-5 relative z-40 p-5 rounded-2xl bg-stone-900/40 border border-stone-800 shadow-inner">
        <label class="block text-xs font-bold text-stone-400 uppercase tracking-wider mb-2">Chart Type</label>
        <select id="chartType" class="w-full bg-stone-900 border border-orange-500 rounded-xl px-4 py-2.5 text-stone-100 font-medium focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500">
            <option value="">Select Chart</option>
            <option value="bar">Bar Chart</option>
            <option value="line">Line Chart</option>
            <option value="pie">Pie Chart</option>
            <option value="scatter">Scatter Plot</option>
        </select>
    </div>'''

content = re.sub(r'<!-- Chart Type Selector.*?</div>\s*</div>\s*</div>', chart_type_html, content, flags=re.DOTALL)

# Simplify select wrappers by removing the fake SVG arrows
content = re.sub(r'<div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-stone-.*?</svg></div>', '', content)

# Remove appearance-none and cursor-pointer from selects to make them standard
content = content.replace('appearance-none', '')
content = content.replace('cursor-pointer', '')

# Replace the script payload entirely with exactly what the user wanted
payload = '''<!-- ───── Data Payload & Scripts ───── -->
<script>
    const columns = {{ columns_json|safe }};
    const rows = {{ rows_json|safe }};
    console.log(columns);
    console.log(rows);
    
    window.APP_DATA = window.APP_DATA || {};
    window.APP_DATA.CHART_DATA_URL = `/dataset/{{ file_id }}/chart-data/`;
</script>
'''

content = re.sub(r'<!-- ───── Data Payload.*?</script>', payload, content, flags=re.DOTALL)

with open('app/templates/analytics_studio.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated analytics_studio.html successfully.")
