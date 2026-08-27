// ClinicCare-Lite client-side behaviour: real-time form validation (a UX
// layer only - the server in app.py/utils/validator.py is still the
// authority and re-checks everything), search filtering, mobile nav, and
// inbox polling. No framework - kept small and dependency-free on purpose.

(function () {
  "use strict";

  var ALLOWED_EXTENSIONS = [".txt", ".csv", ".pdf"];

  // -------------------------------------------------------------------
  // Mobile nav toggle
  // -------------------------------------------------------------------
  var navToggle = document.getElementById("nav-toggle");
  var navLinks = document.getElementById("nav-links");
  if (navToggle && navLinks) {
    navToggle.addEventListener("click", function () {
      var isOpen = navLinks.classList.toggle("nav-open");
      navToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });
  }

  // -------------------------------------------------------------------
  // Register form: live ID-format and password-complexity feedback.
  // Mirrors utils/validator.py's rules so the message a user sees before
  // submitting matches the message they'd get back from the server.
  // -------------------------------------------------------------------
  var registerForm = document.querySelector('[data-validate="register-form"]');
  if (registerForm) {
    var roleSelect = document.getElementById("role-select");
    var userIdInput = document.getElementById("user-id-input");
    var idHint = document.getElementById("id-hint");
    var passwordInput = document.getElementById("password-input");
    var idError = registerForm.querySelector('[data-error-for="user_id"]');
    var passwordError = registerForm.querySelector('[data-error-for="password"]');

    function validateId() {
      var value = userIdInput.value.trim();
      var role = roleSelect.value;
      if (!/^\d{8}$/.test(value)) {
        showError(idError, value ? "ID must be exactly 8 digits." : "");
        return false;
      }
      if (role === "clinician") {
        var ok = value.slice(-4) === "0000";
        showError(idError, ok ? "" : 'Clinician IDs must end in "0000".');
        return ok;
      }
      var year = parseInt(value.slice(-4), 10);
      var ok = year >= 2022 && year <= 2028;
      showError(idError, ok ? "" : "Patient IDs must end in a year between 2022 and 2028.");
      return ok;
    }

    function validatePassword() {
      var value = passwordInput.value;
      var missing = [];
      if (value.length < 8) missing.push("at least 8 characters");
      if (!/[A-Z]/.test(value)) missing.push("an uppercase letter");
      if (!/[a-z]/.test(value)) missing.push("a lowercase letter");
      if (!/\d/.test(value)) missing.push("a digit");
      if (!/[!@#$%^&*]/.test(value)) missing.push("a special character (!@#$%^&*)");
      showError(passwordError, missing.length ? "Missing: " + missing.join(", ") + "." : "");
      return missing.length === 0;
    }

    function updateIdHint() {
      idHint.textContent = roleSelect.value === "clinician"
        ? "User ID (8 digits, ending in 0000, e.g. 12350000)"
        : "User ID (8 digits, ending in a registration year 2022-2028, e.g. 12342024)";
    }

    roleSelect.addEventListener("change", function () { updateIdHint(); validateId(); });
    userIdInput.addEventListener("input", validateId);
    passwordInput.addEventListener("input", validatePassword);
    updateIdHint();
  }

  // -------------------------------------------------------------------
  // File-extension check on any upload marked data-validate-ext -
  // immediate feedback before the round-trip to the server.
  // -------------------------------------------------------------------
  document.querySelectorAll("[data-validate-ext]").forEach(function (input) {
    input.addEventListener("change", function () {
      var errorEl = input.closest("form").querySelector('[data-error-for="attachment"]')
        || input.parentElement.querySelector(".field-error");
      if (!input.files || !input.files.length) {
        if (errorEl) showError(errorEl, "");
        return;
      }
      var name = input.files[0].name.toLowerCase();
      var ok = ALLOWED_EXTENSIONS.some(function (ext) { return name.endsWith(ext); });
      if (errorEl) {
        showError(errorEl, ok ? "" : "Only .txt, .csv, and .pdf files are allowed.");
      }
    });
  });

  function showError(el, message) {
    if (!el) return;
    el.textContent = message;
    el.hidden = !message;
  }

  // -------------------------------------------------------------------
  // Client-side search filter for the inbox's conversation/announcement
  // lists - filters what's already on the page, no round-trip needed.
  // -------------------------------------------------------------------
  document.querySelectorAll("[data-search-target]").forEach(function (input) {
    var list = document.getElementById(input.getAttribute("data-search-target"));
    if (!list) return;
    input.addEventListener("input", function () {
      var query = input.value.trim().toLowerCase();
      list.querySelectorAll("[data-search-text]").forEach(function (item) {
        var text = item.getAttribute("data-search-text");
        item.style.display = !query || text.indexOf(query) !== -1 ? "" : "none";
      });
    });
  });

  // -------------------------------------------------------------------
  // Inbox polling: refreshes the unread badge every 15s without a full
  // page reload - the "periodic polling" alternative to WebSockets the
  // course spec allows for near-real-time messaging.
  // -------------------------------------------------------------------
  var unreadBadge = document.getElementById("unread-badge");
  if (unreadBadge) {
    setInterval(function () {
      fetch("/inbox/poll", { credentials: "same-origin" })
        .then(function (response) { return response.ok ? response.json() : null; })
        .then(function (data) {
          if (!data) return;
          unreadBadge.textContent = data.unread;
          unreadBadge.setAttribute("data-unread", data.unread);
          unreadBadge.classList.toggle("badge-empty", data.unread === 0);
        })
        .catch(function () { /* offline or logged out - just skip this tick */ });
    }, 15000);
  }
})();
