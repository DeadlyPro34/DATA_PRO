// analytics.js
document.addEventListener("DOMContentLoaded", function () {
    populateDropdowns();
    initializeChartControls();
});

function populateDropdowns() {
    const xAxis = document.getElementById("xAxis");
    const yAxis = document.getElementById("yAxis");
    const filterColumn = document.getElementById("filterColumn");
    
    // Fallbacks to either global 'columns' array or APP_DATA
    const availableCols = (typeof columns !== 'undefined') ? columns : (window.APP_DATA && window.APP_DATA.columns) ? window.APP_DATA.columns : [];

    if (!availableCols || availableCols.length === 0) {
        console.error("No columns found");
        return;
    }

    availableCols.forEach(column => {
        const option = document.createElement("option");
        option.value = column;
        option.textContent = column;

        if (xAxis) xAxis.appendChild(option.cloneNode(true));
        if (yAxis) yAxis.appendChild(option.cloneNode(true));
        if (filterColumn) filterColumn.appendChild(option.cloneNode(true));
    });
}

function initializeChartControls() {
    const renderChartBtn = document.getElementById("renderChartBtn");
    const chartTypeSelect = document.getElementById("chartTypeSelect");
    const myChartCanvas = document.getElementById("myChart");
    const chartEmptyMsg = document.getElementById("chartEmptyMsg");
    const xAxis = document.getElementById("xAxis");
    const yAxis = document.getElementById("yAxis");
    
    // Inject Chart Types if they aren't fully hardcoded in HTML
    if (chartTypeSelect && chartTypeSelect.options.length === 0) {
        chartTypeSelect.innerHTML = `
            <option value="bar">Bar</option>
            <option value="line">Line</option>
            <option value="pie">Pie</option>
            <option value="scatter">Scatter</option>
        `;
    }

    let currentChart = null;

    if (renderChartBtn) {
        renderChartBtn.addEventListener("click", async () => {
            if (!xAxis || !xAxis.value) {
                alert("Please select an X-Axis");
                return;
            }

            // For multiselect Y-Axis
            let selectedY = [];
            if (yAxis && yAxis.selectedOptions) {
                selectedY = Array.from(yAxis.selectedOptions).map(opt => opt.value);
            } else if (yAxis && yAxis.value) {
                selectedY = [yAxis.value];
            }

            if (selectedY.length === 0 && chartTypeSelect && chartTypeSelect.value !== 'pie') {
                alert("Please select a Y-Axis");
                return;
            }

            if (window.showLoadingState) window.showLoadingState(renderChartBtn);

            try {
                const chartType = chartTypeSelect ? chartTypeSelect.value : 'bar';
                const aggMode = document.getElementById("aggMode") ? document.getElementById("aggMode").value : "none";
                const chartDataUrl = (window.APP_DATA && window.APP_DATA.CHART_DATA_URL) ? window.APP_DATA.CHART_DATA_URL : `/dataset/${window.APP_DATA?.FILE_ID || 0}/chart-data/`;

                const payload = {
                    chart_type: chartType,
                    x_axis: xAxis.value,
                    y_axes: selectedY,
                    agg_mode: aggMode,
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
                
                if (chartEmptyMsg) chartEmptyMsg.style.display = 'none';
                if (myChartCanvas) myChartCanvas.style.display = 'block';

                if (currentChart) {
                    currentChart.destroy();
                }

                const ctx = myChartCanvas.getContext('2d');
                
                // Construct standard Chart.js datasets
                const datasets = (data.datasets || []).map((ds, i) => ({
                    label: ds.label,
                    data: ds.data,
                    backgroundColor: `hsla(${i * 60 + 200}, 70%, 50%, 0.6)`,
                    borderColor: `hsla(${i * 60 + 200}, 70%, 50%, 1)`,
                    borderWidth: 1,
                    fill: chartType === 'area' || chartType === 'line',
                    tension: (chartType === 'line' || chartType === 'area') ? 0.4 : 0
                }));

                const chartConfig = {
                    type: chartType === 'column' ? 'bar' : (chartType === 'area' ? 'line' : chartType),
                    data: {
                        labels: data.labels,
                        datasets: datasets
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                labels: { color: '#a8a29e' }
                            }
                        },
                        scales: chartType === 'pie' || chartType === 'doughnut' ? {} : {
                            x: {
                                ticks: { color: '#78716c' },
                                grid: { color: 'rgba(255,255,255,0.05)' }
                            },
                            y: {
                                ticks: { color: '#78716c' },
                                grid: { color: 'rgba(255,255,255,0.05)' },
                                beginAtZero: true
                            }
                        }
                    }
                };

                currentChart = new Chart(ctx, chartConfig);

            } catch (error) {
                console.error("Chart Error:", error);
                alert(`Failed to render chart: ${error.message}`);
            } finally {
                if (window.restoreButtonState) window.restoreButtonState(renderChartBtn);
            }
        });
    }
}
