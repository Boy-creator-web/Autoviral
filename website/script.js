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
