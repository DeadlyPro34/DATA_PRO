import re

with open('app/templates/analytics_studio.html', 'r', encoding='utf-8') as f:
    content = f.read()

clean_html = '''<!-- ───── Enhanced Chart Builder ───── -->
<div id="chartBuilderPanel" class="bg-stone-900 border border-stone-800 rounded-3xl p-6 mb-8 shadow-2xl">
    
    <div class="flex items-center gap-3 mb-8">
        <div class="p-2 rounded-xl bg-orange-500 text-white shadow-lg shadow-orange-500/30">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"></path></svg>
        </div>
        <h2 class="text-xl font-bold text-stone-100 tracking-tight">Interactive Chart Builder</h2>
    </div>

    <!-- Controls Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div>
            <label class="block mb-2 text-sm font-semibold text-stone-400 uppercase tracking-wider">
                Chart Type
            </label>
            <select id="chartType" class="w-full p-3 rounded-xl bg-stone-950 border border-stone-800 text-white focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500">
                <option value="">Select Chart</option>
                <option value="bar">Bar Chart</option>
                <option value="line">Line Chart</option>
                <option value="pie">Pie Chart</option>
                <option value="scatter">Scatter Plot</option>
            </select>
        </div>

        <div>
            <label class="block mb-2 text-sm font-semibold text-stone-400 uppercase tracking-wider">
                X-Axis
            </label>
            <select id="xAxis" class="w-full p-3 rounded-xl bg-stone-950 border border-stone-800 text-white focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500"></select>
        </div>

        <div>
            <label class="block mb-2 text-sm font-semibold text-stone-400 uppercase tracking-wider">
                Y-Axis
            </label>
            <select id="yAxis" class="w-full p-3 rounded-xl bg-stone-950 border border-stone-800 text-white focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500"></select>
        </div>

        <div>
            <label class="block mb-2 text-sm font-semibold text-stone-400 uppercase tracking-wider">
                Filter Column
            </label>
            <select id="filterColumn" class="w-full p-3 rounded-xl bg-stone-950 border border-stone-800 text-white focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500"></select>
        </div>
    </div>

    <!-- Render Button -->
    <div class="flex justify-end mb-8">
        <button id="renderChartBtn" class="px-8 py-3 bg-stone-200 text-stone-950 hover:bg-white rounded-xl text-sm font-bold shadow-lg transition-all flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
            Render Chart
        </button>
    </div>

    <!-- Canvas Container -->
    <div id="chartContainer" class="bg-stone-950 border border-stone-800 rounded-2xl p-4 h-[500px] flex items-center justify-center w-full">
        <canvas id="myChart" class="w-full h-full"></canvas>
        <p id="chartEmptyMsg" class="text-stone-500 text-sm">Select columns and click Render Chart to visualize your data.</p>
    </div>
</div>
'''

new_content = re.sub(r'<!-- ───── Enhanced Chart Builder ───── -->.*?<!-- ───── Data Payload & Scripts ───── -->', clean_html + '\n<!-- ───── Data Payload & Scripts ───── -->', content, flags=re.DOTALL)

with open('app/templates/analytics_studio.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Rebuilt HTML layout.")
