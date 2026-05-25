import os

files_to_fix = [
    'data_explorer.html', 'analytics_studio.html', 
    'exports_reports.html', 'ai_insights_page.html',
    'data_profiler.html', 'cleaning_lab.html'
]

for file in files_to_fix:
    path = os.path.join('app/templates', file)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'shared.js' not in content:
            # Replace the specific script tag with shared.js + specific script tag
            module_name = 'explorer.js' if 'explorer' in file else \
                          'analytics.js' if 'analytics' in file else \
                          'exports.js' if 'exports' in file else \
                          'chat.js' if 'ai_insights' in file else \
                          'profiler.js' if 'profiler' in file else \
                          'cleaning.js'
            
            target_str = f"<script src=\"{{% static 'js/{module_name}' %}}\"></script>"
            new_str = f"<script src=\"{{% static 'js/shared.js' %}}\"></script>\n{target_str}"
            
            new_content = content.replace(target_str, new_str)
            if content != new_content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f'Injected shared.js into {file}')
