const form = document.getElementById("intakeForm");
const statusEl = document.getElementById("formStatus");
const yearEl = document.getElementById("year");

if (yearEl) {
  yearEl.textContent = String(new Date().getFullYear());
}

async function submitForm(payload) {
  const response = await fetch("/api/v1/customer-intake/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    const detail = errBody.detail || "Terjadi kesalahan. Silakan coba lagi.";
    throw new Error(detail);
  }
  return response.json();
}

if (form && statusEl) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    statusEl.textContent = "Mengirim data...";
    statusEl.className = "form-status";

    const formData = new FormData(form);
    const payload = {
      full_name: String(formData.get("full_name") || "").trim(),
      email: String(formData.get("email") || "").trim(),
      phone: String(formData.get("phone") || "").trim(),
      business_name: String(formData.get("business_name") || "").trim(),
      niche: String(formData.get("niche") || "").trim(),
      product_name: String(formData.get("product_name") || "").trim(),
      product_category: String(formData.get("product_category") || "").trim(),
      product_price_range: String(formData.get("product_price_range") || "").trim(),
      business_model: String(formData.get("business_model") || "").trim(),
      target_customer_profile: String(formData.get("target_customer_profile") || "").trim(),
      target_region: String(formData.get("target_region") || "").trim(),
      main_platforms: String(formData.get("main_platforms") || "").trim(),
      primary_kpi: String(formData.get("primary_kpi") || "").trim(),
      current_monthly_leads: Number(formData.get("current_monthly_leads") || 0),
      current_conversion_rate_percent: Number(
        formData.get("current_conversion_rate_percent") || 0
      ),
      sales_cycle_days: Number(formData.get("sales_cycle_days") || 0),
      monthly_marketing_budget: Number(formData.get("monthly_marketing_budget") || 0),
      preferred_contact_time: String(formData.get("preferred_contact_time") || "").trim(),
      monthly_revenue_target: Number(formData.get("monthly_revenue_target") || 0),
      preferred_plan: String(formData.get("preferred_plan") || "starter").trim(),
      pain_point: String(formData.get("pain_point") || "").trim(),
      desired_outcome: String(formData.get("desired_outcome") || "").trim(),
      source: "synapsetech.my.id",
    };

    try {
      await submitForm(payload);
      statusEl.textContent =
        "Permintaan berhasil dikirim. Tim kami akan menghubungi Anda secepatnya.";
      statusEl.className = "form-status success";
      form.reset();
    } catch (error) {
      statusEl.textContent = error.message;
      statusEl.className = "form-status error";
    }
  });
}
