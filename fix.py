import os
import re

os.makedirs('app/static/js', exist_ok=True)

templates = {
    'analytics_studio.html': 'analytics.js',
    'data_explorer.html': 'explorer.js',
    'cleaning_lab.html': 'cleaning.js',
    'ai_insights_page.html': 'chat.js',
    'exports_reports.html': 'exports.js'
}

for html_file, js_file in templates.items():
    path = os.path.join('app/templates', html_file)
    if not os.path.exists(path):
        continue
        
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Find the payload and logic
    payload_match = re.search(r'<!-- ───── Data Payload ───── -->\s*<script>(.*?)</script>', text, re.DOTALL)
    logic_match = re.search(r'<!-- ───── App Logic ───── -->\s*<script>(.*?)</script>', text, re.DOTALL)
    
    if payload_match and logic_match:
        payload_js = payload_match.group(1)
        logic_js = logic_match.group(1)
        
        # We will wrap the logic JS in DOMContentLoaded
        js_content = f"// {js_file}\n"
        js_content += "document.addEventListener('DOMContentLoaded', function() {\n"
        
        # Add basic container checks so scripts only run on their page
        if html_file == 'analytics_studio.html':
            js_content += "    if (!document.getElementById('analyticsStudioContainer')) return;\n"
        elif html_file == 'data_explorer.html':
            js_content += "    if (!document.getElementById('singleTableView')) return;\n"
        elif html_file == 'cleaning_lab.html':
            js_content += "    if (!document.getElementById('pipelineStepper')) return;\n"
        elif html_file == 'ai_insights_page.html':
            js_content += "    if (!document.getElementById('chatContainer')) return;\n"
        elif html_file == 'exports_reports.html':
            js_content += "    if (!document.getElementById('exportJsonBtn')) return;\n"
            
        js_content += "    const APP_DATA = window.APP_DATA || {};\n"
        
        # Modify the payload in HTML to assign to window.APP_DATA instead of local variables
        new_payload = "    window.APP_DATA = window.APP_DATA || {};\n"
        
        # Extract variables from payload
        for line in payload_js.split('\n'):
            line = line.strip()
            if line.startswith('const ') or line.startswith('let '):
                # Replace 'const foo = bar;' with 'window.APP_DATA.foo = bar;'
                var_decl = line.split('=')[0].replace('const ', '').replace('let ', '').strip()
                val_decl = line[line.find('='):]
                new_payload += f"    window.APP_DATA.{var_decl} {val_decl}\n"
                
                # Replace occurrences of 'var_decl' with 'APP_DATA.var_decl' in logic_js
                # Use a regex word boundary
                logic_js = re.sub(rf'\b{var_decl}\b', f'APP_DATA.{var_decl}', logic_js)
        
        # Function mappings for global shared.js
        logic_js = re.sub(r'\bshowCustomAlert\b', 'window.showCustomAlert', logic_js)
        logic_js = re.sub(r'\bcloseCustomAlert\b', 'window.closeCustomAlert', logic_js)
        
        if html_file != 'data_explorer.html':  # data_explorer defines its own fmtNum
            logic_js = re.sub(r'\bfmtNum\b', 'window.fmtNum', logic_js)
            
        # For Chart.js safety (analytics.js)
        if html_file == 'analytics_studio.html':
            # ensure Chart exists
            logic_js = logic_js.replace("new Chart(ctx, ", "if (typeof Chart !== 'undefined') new Chart(ctx, ")
            # fix canvas checks
            logic_js = logic_js.replace("const ctx = $chartCanvas.getContext('2d');", "if (!$chartCanvas) return; const ctx = $chartCanvas.getContext('2d');")
            
        # Append logic
        # Indent logic_js by 4 spaces
        indented_logic = '\n'.join('    ' + line for line in logic_js.split('\n'))
        js_content += indented_logic
        js_content += "\n});\n"
        
        # Save JS file
        js_path = os.path.join('app/static/js', js_file)
        with open(js_path, 'w', encoding='utf-8') as f:
            f.write(js_content)
            
        # Update HTML file
        new_text = text[:payload_match.start(1)] + "\n" + new_payload + "\n    " + text[payload_match.end(1):logic_match.start(0)]
        # Add script include
        script_tag = f"\n<script src=\"{{% static 'js/{js_file}' %}}\"></script>\n"
        new_text = new_text + script_tag + text[logic_match.end(0):]
        
        # Ensure {% load static %} is present at top
        if '{% load static %}' not in new_text:
            new_text = '{% load static %}\n' + new_text
            
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_text)
            
        print(f"Processed {html_file} -> {js_file}")

