import re
with open('app/templates/dataset_old.html', 'r', encoding='utf-8') as f:
    old_content = f.read()

# Extract from <!-- ───── Enhanced Chart Builder ───── --> to <!-- ───── Data Table with Tabs ───── -->
match = re.search(r'(<!-- ───── Enhanced Chart Builder ───── -->.*?)(?=<!-- ───── Data Table with Tabs ───── -->)', old_content, re.DOTALL)
if not match:
    print("Failed to find Enhanced Chart Builder in dataset_old.html")
    exit(1)
chart_html = match.group(1).strip()

with open('app/templates/analytics_studio.html', 'r', encoding='utf-8') as f:
    studio_content = f.read()

# Replace from <!-- ───── Enhanced Chart Builder ───── --> to <!-- ───── Data Payload & Scripts ───── -->
new_studio_content = re.sub(
    r'<!-- ───── Enhanced Chart Builder ───── -->.*?<!-- ───── Data Payload & Scripts ───── -->',
    chart_html + '\n\n<!-- ───── Data Payload & Scripts ───── -->',
    studio_content,
    flags=re.DOTALL
)

with open('app/templates/analytics_studio.html', 'w', encoding='utf-8') as f:
    f.write(new_studio_content)

print("analytics_studio.html fixed successfully.")
