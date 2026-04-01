function setupMobileNav() {
  const toggle = document.querySelector("[data-nav-toggle]");
  const nav = document.querySelector("[data-nav]");
  if (!toggle || !nav) return;
  toggle.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
  });
}

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
    let detail = "Terjadi kesalahan server.";
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
      if (Array.isArray(body.detail) && body.detail[0] && body.detail[0].msg) {
        detail = body.detail[0].msg;
      }
    } catch (_err) {
      detail = `HTTP ${response.status}`;
    }
    throw new Error(detail);
  }
  return response.json();
}

function setupPricingCards() {
  const container = document.querySelector("[data-pricing-cards]");
  if (!container) return;
  fetchJson("/api/v1/pricing/")
    .then((plans) => {
      container.innerHTML = "";
      plans.forEach((plan) => {
        const el = document.createElement("article");
        el.className = "card";
        el.innerHTML = `
          <h3>${plan.name}</h3>
          <div class="price">${formatIDR(plan.price_monthly)} <span class="small">/ bulan</span></div>
          <p class="muted">${plan.description}</p>
          <ul class="feature-list">
            <li>Video quota: ${plan.video_quota}</li>
            <li>Campaign quota: ${plan.campaign_quota}</li>
            <li>Scraper quota: ${plan.scraper_quota}</li>
          </ul>
          <a class="btn btn-primary" href="/checkout.html?plan=${encodeURIComponent(plan.code)}">Pilih ${plan.name}</a>
        `;
        container.appendChild(el);
      });
    })
    .catch(() => {
      container.innerHTML =
        '<div class="notice error">Gagal memuat pricing dari API. Silakan coba lagi.</div>';
    });
}

function setupFaq() {
  const items = document.querySelectorAll("[data-faq-item]");
  items.forEach((item) => {
    const button = item.querySelector("button");
    if (!button) return;
    button.addEventListener("click", () => {
      item.classList.toggle("open");
    });
  });
}

function setupCheckout() {
  const form = document.querySelector("[data-checkout-form]");
  if (!form) return;
  const status = document.querySelector("[data-status]");
  const summary = document.querySelector("[data-plan-summary]");
  const submitBtn = form.querySelector("button[type='submit']");

  let selectedPlan = null;

  const params = new URLSearchParams(window.location.search);
  const requestedPlan = params.get("plan");

  const setStatus = (message, type) => {
    if (!status) return;
    status.textContent = message;
    status.className = `notice ${type || ""}`.trim();
  };

  fetchJson("/api/v1/pricing/")
    .then((plans) => {
      const preferred = plans.find((item) => item.code === requestedPlan) || plans[0];
      selectedPlan = preferred;
      if (summary) {
        summary.innerHTML = `
          <strong>${preferred.name}</strong><br />
          ${formatIDR(preferred.price_monthly)} / bulan<br />
          <span class="small">Video ${preferred.video_quota} · Campaign ${preferred.campaign_quota} · Scraper ${preferred.scraper_quota}</span>
        `;
      }
      const hiddenPlan = form.querySelector("input[name='plan_code']");
      if (hiddenPlan) hiddenPlan.value = preferred.code;
    })
    .catch(() => {
      setStatus("Gagal memuat paket pricing.", "error");
    });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!selectedPlan) {
      setStatus("Paket belum siap, silakan refresh halaman.", "error");
      return;
    }
    if (submitBtn) submitBtn.disabled = true;
    setStatus("Memproses pendaftaran dan checkout...", "");

    const data = new FormData(form);
    const payload = {
      full_name: String(data.get("full_name") || "").trim(),
      email: String(data.get("email") || "").trim().toLowerCase(),
      phone: String(data.get("phone") || "").trim(),
      password: String(data.get("password") || ""),
      campaign_goal: String(data.get("campaign_goal") || "").trim(),
      months: Number(data.get("months") || 1),
    };

    try {
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
      const authHeaders = {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      };

      const plans = await fetchJson("/api/v1/pricing/");
      const plan = plans.find((item) => item.code === selectedPlan.code);
      if (!plan) throw new Error("Paket tidak ditemukan.");

      const subscription = await fetchJson("/api/v1/subscriptions/", {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({
          user_id: user.id,
          plan_id: plan.id,
          months: payload.months,
        }),
      });

      const payment = await fetchJson("/api/v1/payments/", {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({
          user_id: user.id,
          subscription_id: subscription.id,
          amount: plan.price_monthly * payload.months,
          provider: "website_checkout",
        }),
      });

      await fetchJson("/api/v1/actions/", {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({
          user_id: user.id,
          action_type: "onboarding_campaign",
          title: `Campaign Goal: ${payload.campaign_goal || "General"}`,
          payload: JSON.stringify({
            source: "website_checkout",
            goal: payload.campaign_goal,
            plan_code: plan.code,
          }),
        }),
      });

      window.location.href =
        `/thank-you.html?flow=checkout&invoice=${encodeURIComponent(payment.invoice_no)}&plan=${encodeURIComponent(plan.code)}`;
    } catch (error) {
      setStatus(`Checkout gagal: ${error.message}`, "error");
      if (submitBtn) submitBtn.disabled = false;
    }
  });
}

function setupContactForm() {
  const form = document.querySelector("[data-contact-form]");
  if (!form) return;
  const status = document.querySelector("[data-contact-status]");
  const button = form.querySelector("button[type='submit']");

  const setStatus = (message, type) => {
    if (!status) return;
    status.textContent = message;
    status.className = `notice ${type || ""}`.trim();
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (button) button.disabled = true;
    setStatus("Mengirim permintaan Anda...", "");

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
      source: "synapsetech.my.id",
    };

    try {
      const created = await fetchJson("/api/v1/customer-intake/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      window.location.href = `/thank-you.html?flow=intake&lead_id=${encodeURIComponent(created.id)}`;
    } catch (error) {
      setStatus(`Gagal kirim permintaan: ${error.message}`, "error");
      if (button) button.disabled = false;
    }
  });
}

setupMobileNav();
setupYear();
setupPricingCards();
setupCheckout();
setupContactForm();
setupFaq();
