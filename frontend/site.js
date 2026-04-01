function setupYear() {
  const yearNodes = document.querySelectorAll("[data-year]");
  const year = String(new Date().getFullYear());
  yearNodes.forEach((node) => {
    node.textContent = year;
  });
}

function formatIDR(value) {
  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    maximumFractionDigits: 0,
  }).format(Number(value || 0));
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
      if (Array.isArray(body.detail) && body.detail[0] && body.detail[0].msg) {
        detail = body.detail[0].msg;
      }
    } catch (_error) {
      detail = `HTTP ${response.status}`;
    }
    throw new Error(detail);
  }
  return response.json();
}

function setStatusText(el, message, tone) {
  if (!el) return;
  el.textContent = message;
  el.className = "status";
  if (tone === "error") el.classList.add("error");
  if (tone === "success") el.classList.add("success");
}

async function createLeadIntake(data) {
  return fetchJson("/api/v1/customer-intake/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

async function loadPricing() {
  return fetchJson("/api/v1/pricing/");
}

function renderPricingCards() {
  const container = document.querySelector("[data-pricing-cards]");
  if (!container) return;
  loadPricing()
    .then((plans) => {
      container.innerHTML = "";
      plans.forEach((plan) => {
        const card = document.createElement("article");
        card.className = "card";
        card.innerHTML = `
          <span class="pill">${plan.code.toUpperCase()}</span>
          <h3>${plan.name}</h3>
          <div class="price">${formatIDR(plan.price_monthly)} <small>/ bulan</small></div>
          <p class="muted">${plan.description || "Paket berlangganan Autoviral."}</p>
          <ul class="list">
            <li>Video quota: ${plan.video_quota}</li>
            <li>Campaign quota: ${plan.campaign_quota}</li>
            <li>Scraper insight: ${plan.scraper_quota}</li>
          </ul>
          <div class="cta-row">
            <a class="btn btn-primary" href="/checkout.html?plan=${encodeURIComponent(plan.code)}">Pilih Paket</a>
          </div>
        `;
        container.appendChild(card);
      });

      const enterprise = document.createElement("article");
      enterprise.className = "card card-enterprise";
      enterprise.innerHTML = `
        <span class="pill">ENTERPRISE</span>
        <h3>Enterprise Autonomous</h3>
        <div class="price">Custom <small>/ bulan</small></div>
        <p class="muted">Untuk volume sangat besar, multi-brand, dan kebutuhan governance tingkat lanjut.</p>
        <ul class="list">
          <li>Custom quota dan orkestrasi workload</li>
          <li>Priority processing + SLA khusus</li>
          <li>Report eksekutif otomatis multi-unit</li>
        </ul>
        <div class="cta-row">
          <a class="btn btn-primary" href="/checkout.html?plan=enterprise">Aktifkan Enterprise</a>
        </div>
      `;
      container.appendChild(enterprise);
    })
    .catch((error) => {
      container.innerHTML = `<div class="status error">Gagal memuat paket: ${error.message}</div>`;
    });
}

function setupHomeLeadForm() {
  const form = document.querySelector("[data-home-lead-form]");
  const statusBox = document.querySelector("[data-home-lead-status]");
  if (!form) return;
  const submitBtn = form.querySelector("button[type='submit']");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (submitBtn) submitBtn.disabled = true;
    setStatusText(statusBox, "Mengirim data Anda...", "");

    const data = new FormData(form);
    const payload = {
      full_name: String(data.get("full_name") || "").trim(),
      email: String(data.get("email") || "").trim().toLowerCase(),
      phone: String(data.get("phone") || "").trim(),
      business_name: String(data.get("business_name") || "").trim(),
      niche: String(data.get("niche") || "").trim(),
      monthly_revenue_target: Number(data.get("monthly_revenue_target") || 0),
      preferred_plan: String(data.get("preferred_plan") || "starter"),
      pain_point: String(data.get("pain_point") || "Perlu otomasi growth").trim(),
      desired_outcome: String(data.get("desired_outcome") || "Meningkatkan konversi").trim(),
      source: "homepage_autonomous",
    };

    try {
      const created = await createLeadIntake(payload);
      window.location.href = `/thank-you.html?flow=home_lead&lead_id=${encodeURIComponent(created.id)}`;
    } catch (error) {
      setStatusText(statusBox, `Gagal kirim data: ${error.message}`, "error");
      if (submitBtn) submitBtn.disabled = false;
    }
  });
}

function setupContactForm() {
  const form = document.querySelector("[data-contact-form]");
  const statusBox = document.querySelector("[data-contact-status]");
  if (!form) return;
  const submitBtn = form.querySelector("button[type='submit']");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (submitBtn) submitBtn.disabled = true;
    setStatusText(statusBox, "Mengirim permintaan Anda...", "");

    const data = new FormData(form);
    const payload = {
      full_name: String(data.get("full_name") || "").trim(),
      email: String(data.get("email") || "").trim(),
      phone: String(data.get("phone") || "").trim(),
      business_name: String(data.get("business_name") || "").trim(),
      niche: String(data.get("niche") || "").trim(),
      monthly_revenue_target: Number(data.get("monthly_revenue_target") || 0),
      preferred_plan: String(data.get("preferred_plan") || "starter"),
      pain_point: String(data.get("pain_point") || "").trim(),
      desired_outcome: String(data.get("desired_outcome") || "").trim(),
      source: "contact_autonomous",
    };

    try {
      const created = await createLeadIntake(payload);
      window.location.href = `/thank-you.html?flow=contact&lead_id=${encodeURIComponent(created.id)}`;
    } catch (error) {
      setStatusText(statusBox, `Gagal kirim form: ${error.message}`, "error");
      if (submitBtn) submitBtn.disabled = false;
    }
  });
}

function setupCheckout() {
  const form = document.querySelector("[data-checkout-form]");
  const statusBox = document.querySelector("[data-checkout-status]");
  const summary = document.querySelector("[data-plan-summary]");
  if (!form) return;

  const submitBtn = form.querySelector("button[type='submit']");
  const planSelect = form.querySelector("select[name='plan_code']");
  const monthsInput = form.querySelector("input[name='months']");

  let planMap = new Map();
  let selectedPlanCode = "starter";

  const query = new URLSearchParams(window.location.search);
  const requestedPlan = (query.get("plan") || "").toLowerCase();

  function refreshSummary() {
    if (!summary) return;
    const selected = planMap.get(selectedPlanCode);
    if (!selected) {
      summary.innerHTML = "<p class='muted'>Memuat paket...</p>";
      return;
    }
    const months = Math.max(1, Number(monthsInput?.value || 1));
    const total = selected.price_monthly * months;
    summary.innerHTML = `
      <h4>${selected.name}</h4>
      <p class="muted">Harga bulanan: ${formatIDR(selected.price_monthly)}</p>
      <p class="muted">Durasi: ${months} bulan</p>
      <p><strong>Total tagihan awal: ${formatIDR(total)}</strong></p>
    `;
  }

  loadPricing()
    .then((plans) => {
      planMap = new Map(plans.map((item) => [item.code.toLowerCase(), item]));
      if (requestedPlan && planMap.has(requestedPlan)) {
        selectedPlanCode = requestedPlan;
      } else if (plans[0]) {
        selectedPlanCode = plans[0].code.toLowerCase();
      }

      if (planSelect) {
        planSelect.innerHTML = plans
          .map((plan) => `<option value="${plan.code.toLowerCase()}">${plan.name} - ${formatIDR(plan.price_monthly)}/bulan</option>`)
          .join("");
        planSelect.innerHTML += '<option value="enterprise">Enterprise Autonomous - Custom</option>';
        planSelect.value = selectedPlanCode;
      }
      refreshSummary();
    })
    .catch((error) => {
      setStatusText(statusBox, `Gagal memuat paket: ${error.message}`, "error");
    });

  if (planSelect) {
    planSelect.addEventListener("change", () => {
      selectedPlanCode = String(planSelect.value || "starter").toLowerCase();
      refreshSummary();
    });
  }
  if (monthsInput) {
    monthsInput.addEventListener("input", refreshSummary);
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (submitBtn) submitBtn.disabled = true;
    setStatusText(statusBox, "Memproses pendaftaran dan pembayaran otomatis...", "");

    const selected = planMap.get(selectedPlanCode);
    if (!selected && selectedPlanCode !== "enterprise") {
      setStatusText(statusBox, "Paket tidak ditemukan.", "error");
      if (submitBtn) submitBtn.disabled = false;
      return;
    }

    const data = new FormData(form);
    const payload = {
      full_name: String(data.get("full_name") || "").trim(),
      email: String(data.get("email") || "").trim().toLowerCase(),
      phone: String(data.get("phone") || "").trim(),
      password: String(data.get("password") || ""),
      business_name: String(data.get("business_name") || "").trim(),
      niche: String(data.get("niche") || "").trim(),
      goal: String(data.get("goal") || "").trim(),
      months: Math.max(1, Number(data.get("months") || 1)),
      plan_code: selectedPlanCode,
    };

    try {
      if (payload.plan_code === "enterprise") {
        const created = await createLeadIntake({
          full_name: payload.full_name,
          email: payload.email,
          phone: payload.phone,
          business_name: payload.business_name,
          niche: payload.niche,
          monthly_revenue_target: Number(data.get("monthly_revenue_target") || 0),
          preferred_plan: "enterprise",
          pain_point: "Enterprise onboarding",
          desired_outcome: payload.goal || "Enterprise autonomous rollout",
          source: "checkout_enterprise",
        });
        window.location.href = `/thank-you.html?flow=enterprise&lead_id=${encodeURIComponent(created.id)}`;
        return;
      }

      const user = await fetchJson("/api/v1/users/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: payload.full_name,
          email: payload.email,
          phone: payload.phone,
          password: payload.password,
        }),
      });

      const loginResp = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          username: payload.email,
          password: payload.password,
        }),
      });
      if (!loginResp.ok) throw new Error("Login gagal setelah registrasi.");
      const loginData = await loginResp.json();
      const token = loginData.access_token;
      if (!token) throw new Error("Token tidak diterima dari server.");

      const authHeaders = {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      };

      const subscription = await fetchJson("/api/v1/subscriptions/", {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({
          user_id: user.id,
          plan_id: selected.id,
          months: payload.months,
        }),
      });

      const payment = await fetchJson("/api/v1/payments/", {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({
          user_id: user.id,
          subscription_id: subscription.id,
          amount: selected.price_monthly * payload.months,
          provider: "website_autonomous_checkout",
        }),
      });

      await fetchJson("/api/v1/actions/", {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({
          user_id: user.id,
          action_type: "autonomous_onboarding",
          title: `Autonomous Goal: ${payload.goal || "Growth"}`,
          payload: JSON.stringify({
            source: "website_autonomous_checkout",
            goal: payload.goal,
            plan_code: selected.code,
            business_name: payload.business_name,
            niche: payload.niche,
          }),
        }),
      });

      window.location.href =
        `/thank-you.html?flow=checkout&invoice=${encodeURIComponent(payment.invoice_no)}&plan=${encodeURIComponent(selected.code)}`;
    } catch (error) {
      setStatusText(statusBox, `Checkout gagal: ${error.message}`, "error");
      if (submitBtn) submitBtn.disabled = false;
    }
  });
}

function setupThankYou() {
  const holder = document.querySelector("[data-thankyou-message]");
  if (!holder) return;

  const params = new URLSearchParams(window.location.search);
  const flow = params.get("flow") || "default";
  const invoice = params.get("invoice");
  const leadId = params.get("lead_id");
  const plan = params.get("plan");

  let message = "Permintaan Anda berhasil diproses oleh sistem autonomous kami.";
  if (flow === "checkout") {
    message = "Pembelian paket berhasil. Sistem sedang menyiapkan workspace dan campaign awal Anda.";
  } else if (flow === "enterprise") {
    message = "Permintaan Enterprise diterima. Sistem akan menyiapkan skema rollout enterprise otomatis.";
  } else if (flow === "contact" || flow === "home_lead") {
    message = "Data Anda berhasil masuk. Sistem akan memproses assessment dan rekomendasi paket otomatis.";
  }

  const details = [];
  if (plan) details.push(`Plan: ${plan.toUpperCase()}`);
  if (invoice) details.push(`Invoice: ${invoice}`);
  if (leadId) details.push(`Lead ID: ${leadId}`);

  holder.innerHTML = `
    <p>${message}</p>
    ${details.length ? `<p class="muted">${details.join(" · ")}</p>` : ""}
  `;
}

setupYear();
renderPricingCards();
setupHomeLeadForm();
setupContactForm();
setupCheckout();
setupThankYou();
