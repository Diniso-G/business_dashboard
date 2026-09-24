if (!requireAuth()) {}

let selectedForCompare = [];

initBusinessSelect(() => loadHistory());
loadHistory();

async function loadHistory() {
    const businessId = getCurrentBusinessId();
    const params = businessId ? `?business_id=${businessId}` : "";
    const resp = await fetch(`/reports${params}`, {headers: authHeaders()});
    const container = document.getElementById("historyTable");

    if (!resp.ok) {container.innerHTML = "<p style='color:var(--slate)'>Couldn't load report history.</p>"; return;}

    const reports = await resp.json();
    selectedForCompare = [];

    if (!reports.length) {
        container.innerHTML = "<p style='color:var(--slate)'>No reports yet in this workspace. <a href=`/dashboard'>Upload one</a> to get started.</p>";
        return;
    }

    container.innerHTML = `<table class="history-full-table"> <thead><tr><th></th><th>File</th><th>Uploaded</th><th>Total revenue</th><th>Avg order value</th><th></th></tr></thead><tbody id="historyTbody"></tbody></table>`;
    const tbody = document.getElementById("historyTbody");

    reports.forEach(r => {
        const tr = document.createElement("tr");
        const date = new Date(r.uploaded_at).toLocaleString();
        tr.innerHTML = `
            <td><input type="checkbox" data-id="${r.id}"></td>
            <td class="hi-name">${r.filename}</td>
            <td>${date}</td>
            <td>$${(r.total_revenue || 0).toLocaleString()}</td>
            <td>$${(r.avg_order_value || 0).toLocaleString()}</td>
            <td> <a href="/dashboard?report=${r.id}" class="btn-small">View</a>
                <button class="btn-small btn-delete-row" data-id="${r.id}" type="button">Delete</button>
            </td>`;

        tr.querySelector('input[type="checkbox"]').addEventListener("click", (e) => {
            if (e.target.checked) selectedForCompare.push(r.id);
            else selectedForCompare = selectedForCompare.filter(x => x !== r.id);
        });
        tr.querySelector(".btn-delete-row").addEventListener("click", () => deleteReport(r.id));
        tbody.appendChild(tr);
    });
}

async function deleteReport(id) {
    if (!confirm("Delete this report? This can't be undone.")) return;
    const resp= await fetch(`/reports/${id}`, {method: "DELETE", headers: authHeaders()});
    if (resp.ok) loadHistory();
    else alert("Couldn't delete that report.");
}

document.getElementById("compareBtn").addEventListener("click", async () => {
    if (selectedForCompare.length !== 2) {alert("Check exactly 2 reports to compare."); return;}
    const [a, b] = selectedForCompare;
    const resp = await fetch(`/reports/compare?a=${a}&b=${b}`, {headers: authHeaders()});

    if (!resp.ok) {alert("Couldn't compare those reports."); return;}
    const data = await resp.json();
    const grid = document.getElementById("compareGrid");
    grid.innerHTML = "";

    Object.entries(data.comparison).forEach(([key, val]) => {
        const changeClass = val.change_pct > 0 ? "up" : val.change_pct < 0 ? "down" : "";
        const arrow = val.change_pct > 0 ? "^" : val.change_pct < 0 ? "v" : "";
        const div = document.createElement("div");
        
        div.className = "compare-metric";
        div.innerHTML = `
            <div class="em-label">${key.replace(/_/g, " ")}</div>
            <div class="em-value">${val.previous}-- ${val.current}</div>
            <div class="cm-change ${changeClass}">${arrow} ${val.change_pct ?? "n/a"}%</div>
            `;
        grid.appendChild(div);
    });
    document.getElementById("compareSection").style.display = "block";
    document.getElementById("compareSection").scrollIntoView({behavior: "smooth"});
});

