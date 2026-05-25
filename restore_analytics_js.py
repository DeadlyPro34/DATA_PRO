import re
with open('app/templates/dataset_old.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Extract the script block using the same logic as split_templates.py
match = re.search(r'(<!-- ───── App Logic ───── -->.*?)(?=<!-- ─────|$)', text, re.DOTALL)
if not match:
    # If not found by comment, just find the script tags starting around line 601
    match = re.search(r'(<script>\s*// ════════════════════════════════════════════════════════════════════════════\s*// 1\. TABLE.*?)</script>', text, re.DOTALL)

if not match:
    print("Could not find the monolithic script in dataset_old.html")
    exit(1)

logic = match.group(1)

# Remove the <script> and </script> tags if they are there
logic = re.sub(r'^<script>', '', logic)
logic = re.sub(r'</script>$', '', logic)

# Add defensive checks as split_templates.py did
logic = logic.replace('qualityScoreNum.textContent', 'if (qualityScoreNum) qualityScoreNum.textContent')
logic = logic.replace('qualityCircle.style', 'if (qualityCircle) qualityCircle.style')
logic = logic.replace('insightsCount.textContent', 'if (insightsCount) insightsCount.textContent')
logic = logic.replace('aiInsightsContainer.innerHTML', 'if (aiInsightsContainer) aiInsightsContainer.innerHTML')
logic = logic.replace('healthMetricsGrid.innerHTML', 'if (healthMetricsGrid) healthMetricsGrid.innerHTML')
logic = logic.replace('messyExcelBanner.classList', 'if (typeof messyExcelBanner !== "undefined" && messyExcelBanner) messyExcelBanner.classList')
logic = logic.replace('messyExcelIssues.innerHTML', 'if (typeof messyExcelIssues !== "undefined" && messyExcelIssues) messyExcelIssues.innerHTML')

# Additional defensive check for table
logic = logic.replace('tableHeader.innerHTML =', 'if (typeof tableHeader !== "undefined" && tableHeader) tableHeader.innerHTML =')
logic = logic.replace('tableBody.innerHTML =', 'if (typeof tableBody !== "undefined" && tableBody) tableBody.innerHTML =')
logic = logic.replace('pageInfoEl.textContent =', 'if (typeof pageInfoEl !== "undefined" && pageInfoEl) pageInfoEl.textContent =')
logic = logic.replace('showingCount.textContent =', 'if (typeof showingCount !== "undefined" && showingCount) showingCount.textContent =')
logic = logic.replace("prevPageBtn.disabled =", "if (typeof prevPageBtn !== 'undefined' && prevPageBtn) prevPageBtn.disabled =")
logic = logic.replace("nextPageBtn.disabled =", "if (typeof nextPageBtn !== 'undefined' && nextPageBtn) nextPageBtn.disabled =")

with open('app/static/js/analytics.js', 'w', encoding='utf-8') as f:
    f.write(logic)

print("analytics.js restored successfully.")
