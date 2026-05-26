import os
import re

# 1. Update templates to remove rows_json
templates_dir = 'app/templates'
for root, _, files in os.walk(templates_dir):
    for f in files:
        if f.endswith('.html'):
            filepath = os.path.join(root, f)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Remove window.APP_DATA.allRows = JSON.parse('{{ rows_json|escapejs }}');
            content = re.sub(r'window\.APP_DATA\.allRows\s*=\s*JSON\.parse\([^)]*rows_json[^)]*\);?\n?', '', content)
            
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(content)

# 2. Update JS files to listen to 'appDataLoaded' instead of 'DOMContentLoaded'
js_dir = 'app/static/js'
for root, _, files in os.walk(js_dir):
    for f in files:
        if f.endswith('.js'):
            filepath = os.path.join(root, f)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            
            content = content.replace("'DOMContentLoaded'", "'appDataLoaded'")
            content = content.replace('"DOMContentLoaded"', "'appDataLoaded'")
            
            # Fix the if (document.readyState === 'loading') logic
            # Because appDataLoaded is fired after fetch, document.readyState will ALWAYS be 'complete'
            # So if we just replaced DOMContentLoaded with appDataLoaded, the else block would run immediately
            # which is BAD because the data isn't fetched yet!
            # Let's completely remove the readyState check and just attach the event listener!
            # Example pattern in js files:
            # if (document.readyState === 'loading') {
            #     document.addEventListener('appDataLoaded', initFunction);
            # } else {
            #     initFunction();
            # }
            # We want to replace it with:
            # document.addEventListener('appDataLoaded', initFunction);
            
            content = re.sub(r"if\s*\(\s*document\.readyState\s*===\s*['\"]loading['\"]\s*\)\s*\{\s*document\.addEventListener\(['\"]appDataLoaded['\"]\s*,\s*([a-zA-Z0-9_]+)\);\s*\}\s*else\s*\{\s*\1\(\);\s*\}", r"document.addEventListener('appDataLoaded', \1);", content)
            
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(content)

print('Updated templates and JS files.')
