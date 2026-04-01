const checkoutForm = document.getElementById("checkoutForm");
const checkoutStatus = document.getElementById("checkoutStatus");
const accountList = document.getElementById("socialAccountsContainer");
const addAccountBtn = document.getElementById("addSocialRowBtn");
const checkoutYear = document.getElementById("year");
const intakeIdInput = checkoutForm?.querySelector('input[name="intake_id"]');

if (checkoutYear) {
  checkoutYear.textContent = String(new Date().getFullYear());
}

function normalizePlatformLabel(platform) {
  const key = String(platform || "").trim().toLowerCase();
  const labels = {
    instagram: "Instagram",
    tiktok: "TikTok",
    youtube: "YouTube",
    facebook: "Facebook",
    x: "X (Twitter)",
    linkedin: "LinkedIn",
  };
  return labels[key] || key || "Platform";
}

function createAccountRow(values = {}) {
  const row = document.createElement("div");
  row.className = "social-account-row";
  row.innerHTML = `
    <div class="form-grid">
      <label>
        Platform
        <select name="platform" required>
          <option value="">Pilih platform</option>
          <option value="instagram">Instagram</option>
          <option value="tiktok">TikTok</option>
          <option value="youtube">YouTube</option>
          <option value="facebook">Facebook</option>
          <option value="x">X (Twitter)</option>
          <option value="linkedin">LinkedIn</option>
        </select>
      </label>
      <label>
        Username
        <input name="username" required maxlength="255" placeholder="Contoh: @brandanda" />
      </label>
      <label>
        Password
        <input
          name="password"
          type="password"
          required
          maxlength="255"
          placeholder="Masukkan password akun sosial"
        />
      </label>
      <label class="checkout-checkbox-inline">
        <input name="autopost_enabled" type="checkbox" checked />
        Aktifkan akun ini untuk autoposting
      </label>
    </div>
    <button type="button" class="btn btn-danger btn-remove-account">Hapus akun</button>
  `;

  const platformEl = row.querySelector('select[name="platform"]');
  const usernameEl = row.querySelector('input[name="username"]');
  const passwordEl = row.querySelector('input[name="password"]');
  const enabledEl = row.querySelector('input[name="autopost_enabled"]');

  if (platformEl && values.platform) {
    platformEl.value = String(values.platform).toLowerCase();
  }
  if (usernameEl && values.username) {
    usernameEl.value = String(values.username);
  }
  if (passwordEl && values.password) {
    passwordEl.value = String(values.password);
  }
  if (enabledEl && typeof values.autopost_enabled === "boolean") {
    enabledEl.checked = values.autopost_enabled;
  }

  const removeBtn = row.querySelector(".btn-remove-account");
  if (removeBtn) {
    removeBtn.addEventListener("click", () => {
      row.remove();
    });
  }
  return row;
}

function collectSocialAccounts() {
  const rows = accountList ? accountList.querySelectorAll(".social-account-row") : [];
  const accounts = [];
  rows.forEach((row) => {
    const platform = row.querySelector('select[name="platform"]')?.value || "";
    const username = row.querySelector('input[name="username"]')?.value || "";
    const password = row.querySelector('input[name="password"]')?.value || "";
    const autopostEnabled = row.querySelector('input[name="autopost_enabled"]')?.checked ?? true;
    if (!platform || !username || !password) {
      return;
    }
    accounts.push({
      platform: platform.trim(),
      username: username.trim(),
      password: password.trim(),
      autopost_enabled: Boolean(autopostEnabled),
    });
  });
  return accounts;
}

async function submitCheckout(payload) {
  const response = await fetch("/api/v1/customer-intake/checkout", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || "Gagal menyimpan data checkout.");
  }
  return response.json();
}

async function fetchCheckout(intakeId) {
  const response = await fetch(`/api/v1/customer-intake/checkout/${intakeId}`);
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.detail || "Gagal memuat data checkout.");
  }
  return response.json();
}

async function hydrateExistingCheckout(intakeId) {
  if (!accountList || !checkoutStatus) {
    return;
  }
  try {
    const payload = await fetchCheckout(intakeId);
    if (!Array.isArray(payload.social_accounts) || payload.social_accounts.length === 0) {
      return;
    }
    accountList.innerHTML = "";
    payload.social_accounts.forEach((item) => {
      const platformLabel = normalizePlatformLabel(item.platform);
      accountList.appendChild(
        createAccountRow({
          platform: item.platform,
          username: item.username,
          password: "",
          autopost_enabled: item.autopost_enabled,
        })
      );
      appendLoadedNotice(platformLabel, item.username);
    });
  } catch {
    // Keep default blank row when data does not exist yet.
  }
}

function appendLoadedNotice(platform, username) {
  if (!checkoutStatus) {
    return;
  }
  checkoutStatus.textContent = `Akun tersimpan terdeteksi: ${platform} (${username}). Isi ulang password jika ingin update.`;
  checkoutStatus.className = "form-status";
}

if (addAccountBtn && accountList) {
  addAccountBtn.addEventListener("click", () => {
    accountList.appendChild(createAccountRow());
  });
}

if (accountList) {
  accountList.appendChild(createAccountRow());
}

if (checkoutForm && checkoutStatus) {
  checkoutForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    checkoutStatus.textContent = "Menyimpan data akun sosial...";
    checkoutStatus.className = "form-status";

    const formData = new FormData(checkoutForm);
    const intakeId = Number(formData.get("intake_id") || 0);
    const socialAccounts = collectSocialAccounts();

    if (!intakeId || intakeId < 1) {
      checkoutStatus.textContent = "Intake ID tidak valid.";
      checkoutStatus.className = "form-status error";
      return;
    }
    if (socialAccounts.length < 1) {
      checkoutStatus.textContent = "Tambahkan minimal 1 akun media sosial.";
      checkoutStatus.className = "form-status error";
      return;
    }

    try {
      const result = await submitCheckout({
        intake_id: intakeId,
        payment_method: String(formData.get("payment_method") || "midtrans").trim(),
        preferred_plan: String(formData.get("preferred_plan") || "growth").trim(),
        social_accounts: socialAccounts,
      });
      checkoutStatus.textContent = `Checkout tersimpan. ${result.social_accounts_count} akun sosial siap untuk pipeline autoposting.`;
      checkoutStatus.className = "form-status success";
    } catch (error) {
      checkoutStatus.textContent = error.message;
      checkoutStatus.className = "form-status error";
    }
  });
}

if (intakeIdInput) {
  const params = new URLSearchParams(window.location.search);
  const qIntakeId = params.get("intake_id");
  if (qIntakeId && /^\d+$/.test(qIntakeId)) {
    intakeIdInput.value = qIntakeId;
    hydrateExistingCheckout(Number(qIntakeId));
  }
}
