const form = document.getElementById("intakeForm");
const statusEl = document.getElementById("formStatus");
const yearEl = document.getElementById("year");
const aiCsForm = document.getElementById("aiCsForm");
const aiCsStatusEl = document.getElementById("aiCsStatus");
const aiCsMessages = document.getElementById("aiCsMessages");
const aiCsInput = document.getElementById("aiCsInput");
const aiCsCustomerName = document.getElementById("aiCsCustomerName");
const aiCsBusinessName = document.getElementById("aiCsBusinessName");
const aiCsEmail = document.getElementById("aiCsEmail");

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

async function submitAiCs(payload) {
  const response = await fetch("/api/v1/customer-intake/ai-cs/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    const detail = errBody.detail || "AI CS sedang tidak tersedia. Silakan coba lagi.";
    throw new Error(detail);
  }
  return response.json();
}

function appendChatMessage(role, text) {
  if (!aiCsMessages) {
    return;
  }
  const bubble = document.createElement("div");
  bubble.className = role === "user" ? "ai-cs-message user" : "ai-cs-message ai";
  bubble.textContent = text;
  aiCsMessages.appendChild(bubble);
  aiCsMessages.scrollTop = aiCsMessages.scrollHeight;
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
        "Permintaan berhasil dikirim. AI workflow onboarding telah aktif dan siap diproses.";
      statusEl.className = "form-status success";
      form.reset();
    } catch (error) {
      statusEl.textContent = error.message;
      statusEl.className = "form-status error";
    }
  });
}

if (aiCsForm && aiCsStatusEl && aiCsInput) {
  aiCsForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = String(aiCsInput.value || "").trim();
    if (!message) {
      aiCsStatusEl.textContent = "Tulis pesan terlebih dahulu.";
      aiCsStatusEl.className = "form-status error";
      return;
    }

    appendChatMessage("user", message);
    aiCsStatusEl.textContent = "AI CS sedang menyusun jawaban...";
    aiCsStatusEl.className = "form-status";

    try {
      const response = await submitAiCs({
        message,
        customer_name: String(aiCsCustomerName?.value || "").trim() || null,
        business_name: String(aiCsBusinessName?.value || "").trim() || null,
        email: String(aiCsEmail?.value || "").trim() || null,
        source: "synapsetech.my.id",
      });

      let aiReply = response.reply;
      if (Array.isArray(response.suggested_actions) && response.suggested_actions.length > 0) {
        const numbered = response.suggested_actions
          .map((item, index) => `${index + 1}. ${item}`)
          .join("\n");
        aiReply += `\n\nLangkah yang disarankan:\n${numbered}`;
      }
      appendChatMessage("ai", aiReply);
      aiCsStatusEl.textContent = "Jawaban AI CS diterima.";
      aiCsStatusEl.className = "form-status success";
      aiCsInput.value = "";
      aiCsInput.focus();
    } catch (error) {
      aiCsStatusEl.textContent = error.message;
      aiCsStatusEl.className = "form-status error";
    }
  });
}
