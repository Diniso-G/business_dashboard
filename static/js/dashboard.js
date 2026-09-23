if (!requireAuth()) {}

let currentReportId = null;
let chatHistory = [];
let pendingFiles = null;
const EXPECTED_FIELDS = ["date", "product", "units", "revenue", "customer", "status"];

initBusinessSelect(() => loadOverallTrend());
loadOverallTrend();

const requestedReportId = new URLSearchParams(window.location.search).get("report");
if(requestedReportId) {
    fetch(`/reports/${requestedReportId}`, { headers: authHeaders()}).then(r => r.ok ? r.json() : Promise.reject())
        .then(data => renderResults(data)).catch(() => {});
}

function animateCount(sem, target, prefix) {
    const dura = 800;
    const strt = performance.now();
    const frm= 0;
    function step(now) {
        const p = Math.min((now - strt) / dura, 1);
        const ease = 1 - Math.pow(1 - p, 3);
        sem.textContent = prefix + Math.round(frm + (target - frm) * ease).toLocaleString();

        if (p<1)
            requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

function reveal(sem) {
    requestAnimationFrame(() => sem.classList.add("visible"));
}

const resdiv = document.getElementById("results");

document.getElementById("fileInput").addEventListener("change", (e) => {
    const n = e.target.files.length;
    document.getElementById("fileLabel").textContent = n ? `${n} file(s) selected` : "Choose file(s) or drag them here";
});

document.getElementById("analyseBtn").addEventListener("click", async () => {
    const fileInput = document.getElementById("fileInput");
    if (!fileInput.files.length){
        alert("Please choose atleast one file first.");
        return;
    }
    pendingFiles = fileInput.files;
    await runUpload(null);
});

async function runUpload(columnMapping) {
    const stbar = document.getElementById("statusBar");
    stbar.className = "show";
    document.getElementById("statusSpinner").style.display = "block";
    document.getElementById("statusText").textContent = "Analysing your data...";
    document.getElementById("analyseBtn").disabled = true;

    const formData = new FormData();
    for (const f of pendingFiles) formData.append("files", f);

    const businessId = getCurrentBusinessId();
    if (businessId) formData.append("business_id", businessId);
    if (columnMapping) formData.append("column_mapping", JSON.stringify(columnMapping));

    const startDate = document.getElementById("startDate").value;
    const endDate = document.getElementById("endDate").value;

    if (startDate) formData.append("start_date", startDate);
    if (endDate) formData.append("end_date", endDate);

    try{
        const respo = await fetch("/upload", {
            method: "POST",headers: authHeaders(), body: formData});
        document.getElementById("analyseBtn").disabled = false;
        if (!respo.ok){
            const errText = await respo.text();
            stbar.className = "show error";
            document.getElementById("statusSpinner").style.display = "none";
            document.getElementById("statusText").textContent = "Error: " + errText;
            return;
        }
                
        const data = await respo.json();

        if (data.mapping_required) {
            stbar.className = "";
            showMappingModal(data.detected_columns);
            return;
        }

        stbar.className = "";
        renderResults(data);
        loadOverallTrend();

    } catch (err){
        stbar.className = "show error";
        document.getElementById("statusSpinner").style.display = "none";
        document.getElementById("statusText").textContent = "Network error: " + err.message;
        document.getElementById("analyseBtn").disabled = false;

    }
}
   
function showMappingModal(info) {
    document.getElementById("missingFieldsText").textContent = info.missing.join(", ");
    const container = document.getElementById("mappingFields");
    container.innerHTML = "";
    EXPECTED_FIELDS.forEach(field => {
        const wrap = document.createElement("div");
        wrap.className = "form-group";
        const label = document.createElement("label");
        label.textContent = field;
        label.style.textAlign = "left";
        const select = document.createElement("select");
        select.id = "map_" + field;
        select.innerHTML = '<option value=""> -- not present -- </option>' + info.raw_columns.map(c => `<option value="${c}">${c}</option>`).join("");
        wrap.appendChild(label);
        wrap.appendChild(select);
        container.appendChild(wrap);
    });
    openModal("mappingModal");
}
document.getElementById("mappingCancelBtn").addEventListener("click", () => closeModal("mappingModal"));
document.getElementById("mappingSubmitBtn").addEventListener("click", async () => {
    const mapping = {};
    EXPECTED_FIELDS.forEach(field => {
        const val = document.getElementById("map_" + field).value;
        if (val) mapping[field] = val;
    });
    closeModal("mappingModal");
    await runUpload(mapping);
});

function renderResults(data) {
    currentReportId = data.resport_id || null;
    chatHistory = [];
    document.getElementById("chatLog").innerHTML = "";
    resdiv.style.display = "block";

    if (data.total_revenue !== undefined) {
        animateCount(document.getElementById("valRevenue"), data.total_revenue, "$");
    }
    if (data.avg_order_value !== undefined) {
        animateCount(document.getElementById("valAvg"), data.avg_order_value, "$");
    }
    if (data.best_sellers !== undefined) {
        document.getElementById("valTop").textContent = Object.keys(data.best_sellers)[0] || "-";
    }

    ["metricRevenue", "metricAvg", "metricTop"].forEach(id => reveal(document.getElementById(id)));

    const extra = document.getElementById("extraMetrics");
    extra.innerHTML = "";
    const extraDefs = [
        ["transaction_count", "Transactions", v => v],
        ["revenue_growth_pct", "Revenue growth", v => v + "%"],
        ["busiest_month", "Busiest month", v => v],
        ["busiest_day_of_week", "Busiest day", v => v],
        ["unique_customers", "Unique customers", v => v],
        ["refund_rate_pct", "Refund rate", v => v + "%"],

    ];
    extraDefs.forEach(([key, label, fmt]) => {
        if (data[key] === undefined || data[key] === null) return;
        const card = document.createElement("div");
        card.className = "extra-metric";
        card.innerHTML = `<div class="em-label">${label}</div><div class="em-value">${fmt(data[key])}</div>`;
        extra.appendChild(card);
    });

    const anomalySection = document.getElementById("anomalySection");
    const anomalyList = document.getElementById("anomalyList");
    anomalyList.innerHTML = "";

    if (data.anomalies && data.anomalies.length) {
        anomalySection.style.display = "block";
        data.anomalies.forEach(a => {
            const li = document.createElement("li");
            li.className = a.direction === "spike" ? "spike" : "";
            li.textContent = `${a.label}: ${a.direction} to $(${a.value.toLocaleString()} (z=${a.z_score})`;
            anomalyList.append(li);
        });
    } else {
        anomalySection.style.display = "none";
    }

    document.getElementById("chartsLoading").classList.add("show");
    setTimeout(() => {
        if (data.charts){
            if (data.charts.revenue_trend){
                Plotly.newPlot("chart__revenue", data.charts.revenue_trend.data, data.charts.revenue_trend.layout);
                reveal(document.getElementById("chartRevenueCard"));
            }
            if (data.charts.best_sellers){
                Plotly.newPlot("chart__bestsellers", data.charts.best_sellers.data, data.charts.best_sellers.layout);
                reveal(document.getElementById("chartBestCard"));
            }
            if (data.charts.revenue_by_day){
                document.getElementById("chartsDayCard").style.display = "block";
                Plotly.newPlot("chart__byday", data.charts.revenue_by_day.data, data.charts.revenue_by_day.layout);
                reveal(document.getElementById("chartDayCard"));
            }
            else {
                document.getElementById("chartDayCard").style.display = "none";
            }
        }
        document.getElementById("chartsLoading").classList.remove("show");
    }, 150);

    document.getElementById("aiLoading").classList.add("show");
    setTimeout(() => {
        if (data.ai_recommendations){
            document.getElementById("aiText").textContent = data.ai_recommendations;
            reveal(document.getElementById("aiCard"));
        }
        document.getElementById("aiLoading").classList.remove("show");
    }, 150);

    if (currentReportId) {
        document.getElementById("exportCsvBtn").href = `/reports/${currentReportId}/export.csv`;
        document.getElementById("exportPdfBtn").href = `/reports/${currentReportId}/export.pdf`;
    }
}

async function loadOverallTrend() {
    const businessId = getCurrentBusinessId();
    const params = businessId ? `?business_id=${businessId}` : "";
    const resp = await fetch(`/reports/trend${params}`, {headers: authHeaders()});

    if (!resp.ok) return;
    const data = await resp.json();

    if (!data.points.length) {
        Plotly.purge("charts__overalltrend");
        return;
    }

    const x = data.points.map(p => p.uploaded_at.slice(0, 10));
    const y = data.points.map(p => p.total_revenue);
    Plotly.newPlot("chart__overalltrend", [{x, y, type: "scatter", mode: "lines+markers", line: {color: "#3b83f6"}}], {
        margin: {t: 10, b:40, l: 50, r: 10}, paper_bgcolor: "transparent", plot_bgcolor: "transparent", height: 220,
        xaxis: {color: "#94a3b8"}, yaxis: {color: "#94a3b8"}
    });
}

document.getElementById("chatSendBtn").addEventListener("click", sendChat);
document.getElementById("chatInput").addEventListener("keydown", (e) => {if (e.key === "Enter") sendChat();});

async function sendChat() {
    if (!currentReportId) {
        alert("Analyse a report first."); return;
    }

    const input = document.getElementById("chatInput");
    const question = input.value.trim();
    if (!question) return;
    input.value = "";

    const log = document.getElementById("chatLog");
    log.innerHTML += `<div class="chat-msg user"><b>You:</b> ${question}</div>`;
    log.scrollTop = log.scrollHeight;
    chatHistory.push({ role: "user", content: question});

    const reps = await fetch(`/reports/${currentReportId}/chat`, {
        method: "POST", headers: authHeaders({"Content-Type": "application/json"}),
        body: JSON.stringify({question, history: chatHistory})
    });
    const data = await resp.json();
    log.innerHTML += `<div class="chat-msg assistant"><b>Assistant:<b> ${data.answer}</div>`;
    log.scrollTop = log.scrollHeight;
    chatHistory.push({role: "assistant", content: data.amswer});
}

document.getElementById("importSheetBtn").addEventListener("click", () => openModal("sheetModal"));
document.getElementById("sheetCancelBtn").addEventListener("click", () => closeModal("sheetModal"));
document.getElementById("sheetSubmitBtn").addEventListener("click", async () => {
    const sheetUrl = document.getElementById("sheetUrl").value.trim();
    if (!sheetUrl) return;
    closeModal("sheetModal");
    await runImport("/import/google-sheet", {sheet_url: sheetUrl});
});

document.getElementById("importStripeBtn").addEventListener("click", () => openModal("stripeModal"));
document.getElementById("stripeCancelBtn").addEventListener("click", () => closeModal("stripeModal"));
document.getElementById("stripeSubmitBtn").addEventListener("click", async () => {
    const secretKey = document.getElementById("stripeJey").value.trim();
    if (!secretKey) return;
    closeModal("stripeModal");
    await runImport("/import/stripe", {secret_key: secretKey});
});

document.getElementById("importShopifyBtn").addEventListener("click", () => openModal("shopifyModal"));
document.getElementById("shopifyCancelBtn").addEventListener("click", () => closeModal("shopifyModal"));
document.getElementById("shopifySubmitBtn").addEventListener("click", async () => {
    const shop_domain = document.getElementById("shopifyDomain").value.trim();
    const access_token = document.getElementById("shopifyToken").value.trim();
    if (!shop_domain || !access_token) return;
    closeModal("shopifyModal");
    await runImport("/import/shopify", {shop_domain, access_token});
});

async function runImport(endpoint, fields) {
    const stbar = document.getElementById("statusBar");
    stbar.className = "show";
    document.getElementById("statusSpinner").style.display = "block";
    document.getElementById("statusText").textContent = "Importing data...";

    const formData = new FormData();
    Object.entries(fields).forEach(([k, v]) => formData.append(k, v));
    const businessId = getCurrentBusinessId();
    if (businessId) formData.append("business_id", businessId);

    try {
        const reps = await fetch(endpoint, {method: "POST", headers: authHeaders(), body: formData});
        const data = await resp.json();
        if (!resp.ok) {
            stbar.className = "show error";
            document.getElementById("statusSpinner").style.display = "none";
            document.getElementById("statusText").textContent = "Error: " + (data.detail || "import failed");
            return;
        }
        stbar.className = "";
        if (data.mapping_required) {showMappingModal(data.detected_columns); return; }
        renderResults(data);
        loadOverallTrend();
    } catch (err) {
        stbar.className = "show error";
        document.getElementById("statusSpinner").style.display = "none";
        document.getElementById("statusText").textContent = "Network Error: " + err.message;    
    }
}


