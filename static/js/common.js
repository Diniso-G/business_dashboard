function authToken() {
    return localStorage.getItem("authToken");
}

function authHeaders(extra) {
    return Object.assign({ "Authorization": "Bearer " + authToken() }, extra || {});
}

function requireAuth() {
    if (!authToken()) {
        window.location.href = "/";
        return false;
    }
    const emailEl = document.getElementById("userEmailDisplay");
    if (emailEl) emailEl.textContent = localStorage.getItem("userEmail") || "";
    return true;
}

function logout() {
    localStorage.removeItem("authToken");
    localStorage.removeItem("userEmail");
    localStorage.removeItem("currentBusinessId");
    window.location.href = "/";
}

function wireLogoutButton() {
    const btn = document.getElementById("logoutBtn");
    if (btn) btn.addEventListener("click", logout);
}

function highlightActiveNav() {
    const path = window.location.pathname.replace("/", "") || "dashboard";
    document.querySelectorAll("[data-nav]").forEach(link => {
        if (link.dataset.nav === path) link.classList.add("active");
    });
}

function getCurrentBusinessId() {
    return localStorage.getItem("currentBusinessId") || "";
}

function setCurrentBusinessId(id) {
    if (id) localStorage.setItem("currentBusinessId", id);
    else localStorage.removeItem("currentBusinessId");
}

async function initBusinessSelect(onChange) {
    const select = document.getElementById("businessSelect");
    if (!select) return;
    try {
        const resp = await fetch("/businesses", {headers: authHeaders() });
        if (!resp.ok) return;
        const businesses = await resp.json();
        select.innerHTML = '<option value="">Personal (no workspace)</option>';
        businesses.forEach(b => {
            const opt = document.createElement("option");
            opt.value = b.id;
            opt.textContent = b.name + (b.is_owner ? "" : " (shared)");
            select.appendChild(opt);
        });
        select.value = getCurrentBusinessId();
    } catch (e) {}
    select.addEventListener("change", (e) => {
        setCurrentBusinessId(e.target.value);
        if (onChange) onChange(e.target.value);
    });
}

function openModal(id) { document.getElementById(id).classList.add("show");}
function closeModal(id) { document.getElementById(id).classList.remove("show");}

document.addEventListener("DOMContentLoaded", () => {
    wireLogoutButton();
    highlightActiveNav();
});
