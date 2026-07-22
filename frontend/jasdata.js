const API = "http://127.0.0.1:8000";

/* -------------------------------
   CROP RECOMMENDATION
--------------------------------*/
async function predictCrop() {
    const data = {
        nitrogen: +n.value,
        phosphorus: +p.value,
        potassium: +k.value,
        temperature: +temp.value,
        humidity: +hum.value,
        ph: +ph.value,
        rainfall: +rain.value
    };

    const res = await fetch(`${API}/predict-crop`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });

    const result = await res.json();

    if (result.error) {
        cropResult.innerText = `Error: ${result.error}`;
        return;
    }

    cropResult.innerText =
        `Recommended Crop: ${result.recommended_crop} 
Confidence: ${(result.confidence * 100).toFixed(2)}%`;

    if (typeof recordHistory === 'function') {
        recordHistory(`Crop recommended: ${result.recommended_crop}`);
    }
}

/* -------------------------------
   CURRENT MARKET PRICE
--------------------------------*/
async function getPrice() {
    const res = await fetch(`${API}/get-current-price`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            crop: cropName.value,
            state: "Telangana",
            market: "Hyderabad"
        })
    });

    const data = await res.json();

    if (data.error) {
        priceResult.innerText = `Error: ${data.error}`;
        return;
    }

    priceResult.innerText =
        `₹${data.price} / Quintal | Market: ${data.market} | State: ${data.state || 'N/A'} | Date: ${data.date}`;

    if (typeof recordHistory === 'function') {
        recordHistory(`Queried price for ${cropName.value}`);
    }

    // Call price prediction (year-wise: 2024 to 2030)
    predictPrice(cropName.value, 'years', 0, false, 2024, 2030);
}

/* -------------------------------
   PRICE PREDICTION
--------------------------------*/
async function predictPrice(crop, period = 'days', count = 7, includeHistory = false, startYear = null, endYear = null) {
    const res = await fetch(`${API}/predict-price`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            crop: crop,
            days: count,
            period: period,
            include_history: includeHistory,
            start_year: startYear,
            end_year: endYear
        })
    });

    const data = await res.json();

    if (data.error) {
        console.error("Price prediction error:", data.error);
        return;
    }

    drawChart(data.dates, data.prices);
}

/* -------------------------------
   PROFIT ESTIMATION
--------------------------------*/
async function estimateProfit() {
    const res = await fetch(`${API}/estimate-profit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            price: +price.value,
            yield_amount: +yield.value,
            fertilizer_cost: +fertilizer.value,
            irrigation_cost: +irrigation.value
        })
    });

    const data = await res.json();

    if (data.error) {
        profitResult.innerText = `Error: ${data.error}`;
        return;
    }

    profitResult.innerText =
        `Expected Profit: ₹${data.expected_profit}`;

    if (typeof recordHistory === 'function') {
        recordHistory(`Profit estimated: ₹${data.expected_profit}`);
    }
}

/* -------------------------------
   BAR CHART (Chart.js)
--------------------------------*/
let chart;

function drawChart(labels, prices) {
    const ctx = document.getElementById("priceChart").getContext("2d");

    // Destroy old chart
    if (chart) chart.destroy();

    chart = new Chart(ctx, {
        type: "bar",   // ✅ Bar Graph
        data: {
            labels: labels,
            datasets: [{
                label: "Predicted Crop Price (₹)",
                data: prices,

                // Bar colors
                backgroundColor: "rgba(54, 162, 235, 0.6)",
                borderColor: "rgba(54, 162, 235, 1)",
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return "₹ " + context.raw;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: "Price (₹)"
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: "Date"
                    }
                }
            }
        }
    });
}