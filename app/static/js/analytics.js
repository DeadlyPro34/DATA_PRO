// analytics.js
document.addEventListener("DOMContentLoaded", function () {
    console.log("Analytics Studio initialized");
    
    populateDropdown("xAxis");
    populateDropdown("yAxis");
    populateDropdown("filterColumn");

    const renderChartBtn = document.getElementById("renderChartBtn");
    if (renderChartBtn) {
        renderChartBtn.addEventListener("click", renderChart);
    }
});

function populateDropdown(selectId) {
    const select = document.getElementById(selectId);
    if (!select) return;

    if (typeof columns === 'undefined' || !columns || columns.length === 0) return;

    columns.forEach(column => {
        const option = document.createElement("option");
        option.value = column;
        option.textContent = column;
        select.appendChild(option);
    });
}

let currentChart = null;

async function renderChart() {
    const chartType = document.getElementById("chartType").value;
    const xAxis = document.getElementById("xAxis").value;
    const yAxis = document.getElementById("yAxis").value;

    if (!chartType) {
        alert("Please select a Chart Type");
        return;
    }
    if (!xAxis) {
        alert("Please select an X-Axis");
        return;
    }
    if (!yAxis && chartType !== "pie") {
        alert("Please select a Y-Axis");
        return;
    }

    const renderChartBtn = document.getElementById("renderChartBtn");
    if (window.showLoadingState) window.showLoadingState(renderChartBtn);

    try {
        const chartDataUrl = window.APP_DATA?.CHART_DATA_URL || '';
        
        const payload = {
            chart_type: chartType,
            x_axis: xAxis,
            y_axes: yAxis ? [yAxis] : [],
            agg_mode: "sum",
            time_group: "",
            filters: [],
            top_n: 50
        };

        const csrf = window.getCsrfToken ? window.getCsrfToken() : '';
        const response = await fetch(chartDataUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || `HTTP ${response.status}`);
        }

        const data = await response.json();
        
        const myChartCanvas = document.getElementById("myChart");
        const chartEmptyMsg = document.getElementById("chartEmptyMsg");

        if (chartEmptyMsg) chartEmptyMsg.style.display = 'none';
        
        if (currentChart) {
            currentChart.destroy();
        }

        const ctx = myChartCanvas.getContext('2d');
        
        const datasets = (data.datasets || []).map((ds, i) => ({
            label: ds.label,
            data: ds.data,
            backgroundColor: `hsla(${i * 60 + 200}, 70%, 50%, 0.6)`,
            borderColor: `hsla(${i * 60 + 200}, 70%, 50%, 1)`,
            borderWidth: 1,
            fill: chartType === 'line' || chartType === 'area',
            tension: 0.1
        }));

        let jsChartType = chartType === 'column' ? 'bar' : (chartType === 'area' ? 'line' : chartType);

        const chartConfig = {
            type: jsChartType,
            data: {
                labels: data.labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#a8a29e' } }
                }
            }
        };

        currentChart = new Chart(ctx, chartConfig);

    } catch (error) {
        console.error("Chart Rendering Error:", error);
        alert(`Failed to render chart: ${error.message}`);
    } finally {
        if (window.restoreButtonState) window.restoreButtonState(renderChartBtn);
    }
}
