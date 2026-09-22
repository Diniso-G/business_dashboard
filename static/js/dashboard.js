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
}


