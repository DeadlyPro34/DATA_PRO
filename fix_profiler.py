with open('app/templates/data_profiler.html', 'r', encoding='utf-8') as f:
    content = f.read()

payload = """<!-- ───── Data Payload ───── -->
<script>
    window.APP_DATA = window.APP_DATA || {};
    window.APP_DATA.columns = JSON.parse('{{ columns_json|escapejs|default:"[]" }}');
    window.APP_DATA.uniqueColumns = JSON.parse('{{ unique_columns_json|escapejs|default:"[]" }}');
    window.APP_DATA.allRows = JSON.parse('{{ rows_json|escapejs|default:"[]" }}');
    window.APP_DATA.FILE_ID = {{ file_id }};
    window.APP_DATA.CHART_DATA_URL = `/dataset/${window.APP_DATA.FILE_ID}/chart-data/`;
    window.APP_DATA.ADVANCED_STATS_URL = `/dataset/${window.APP_DATA.FILE_ID}/advanced-stats/`;
    window.APP_DATA.stats = JSON.parse('{{ stats_json|escapejs|default:"{}" }}');
</script>
"""

if '<!-- ───── Data Payload ───── -->' not in content:
    new_content = content.replace("<script src=\"{% static 'js/profiler.js' %}\"></script>", payload + "\n<script src=\"{% static 'js/profiler.js' %}\"></script>")
    with open('app/templates/data_profiler.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Injected APP_DATA into data_profiler.html')
