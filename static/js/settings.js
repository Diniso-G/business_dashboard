if (!requireAuth()) {}

let managingBusinessId = getCurrentBusinessId() || null;

loadBusinesses();

async function loadBusinesses() {
    const resp = await fetch(`/businesses`, {headers: authHeaders()});
    const container = document.getElementById("businessList");

    if (!resp.ok) {container.innerHTML = "<p style='color:var(--slate)'>Couldn't load workspaces.</p>"; return;}

    const businesses = await resp.json();
    selectedForCompare = [];

    if (!businesses.length) {
        container.innerHTML = "<p style='color:var(--slate)'>No workspaces yet. Create one below, or just use analytics personally without one.</p>";
        return;
    }

    container.innerHTML = "";
    businesses.forEach(b => {
        const row = document.createElement("div");
        row.className = "workspace-row" + (b.id == managingBusinessId ? " active" : "");
        row.innerHTML = `
            <span>${b.name}</span>
            <span class="role-badge">${b.is_owner ? "Owner" : "Member"}</span>`;

        row.addEventListener("click", () => {
            managingBusinessId = b.id;
            document.querySelectorAll(".workspace-row").forEach(el => el.classList.remove("active"));
            row.classList.add("active");
            document.getElementById("selectedBusinessLabel").textContent = `- ${b.name}`;
            loadMembers();
        });
        container.appendChild(row);
    });
    if (managingBusinessId) loadMembers();
}

document.getElementById("createBusinessBtn").addEventListener("click", async () => {
    const name = document.getElementById("newBusinessName").value.trim();
    if (!name) return;
    const resp = await fetch("/businesses", {
        method: "POST", headers: authHeaders({ "Content-Type": "application/json"}),
        body: JSON.stringify({name})
    });

    if (resp.ok) {
        const created = await resp.json();
        document.getElementById("newBusinessName").value = "";
        managingBusinessId = created.id;
        document.getElementById("selectedBusinessLabel").textContent = `- ${created.name}`;
        loadBusinesses();
    }else {
        alert("Couldn't create workspace.");
    }
});

async function loadMembers() {
    const container = document.getElementById("memberList");
    if (!managingBusinessId) {container.innerHTML = ""; return;}
    const resp = await fetch(`/businesses/${managingBusinessId}/members`, {headers: authHeaders()});

    if (!resp.ok) {container.innerHTML = "<p style='color: var(--slate)'>Couldn't load members.</p>"; return; }
    const members = await resp.json();
    container.innerHTML = members.map(m => 
        `<div class="member-row"><span>${m.email}</span><span class="role-badge">${m.role}</span></div>`
    ).join("") || "<p style='color:var(--slate);font-size:13px;'>No members yets.</p>";
}

document.getElementById("inviteBtn").addEventListener("click", async () => {
    if (!managingBusinessId) {alert("Select a workspace above first."); return;}
    const targetName = document.querySelector(".workspace-row.active span")?.textContent || `workspace #${managingBusinessId}`;
    const email = document.getElementById("inviteEmail").value.trim();
    if (!email) return;
    if (!confirm(`Invite ${email} to "${targetName}"?`)) return;
    const resp = await fetch(`/businesses/${managingBusinessId}/invite`, {method: "POST", headers: authHeaders({"Content-Type" : "application/json"}), body: JSON.stringify({email})
    });

    const data = await resp.json();
    alert(data.message || data.detail || "Done.");
    if (resp.ok) {
        document.getElementById("inviteEmail").value = "";
        loadMembers();
    }
});

