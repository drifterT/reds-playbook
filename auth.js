(function(){
  "use strict";

  const AUTH_KEY = "redsPlaybookAuth";
  const AUTH_TIME_KEY = "redsPlaybookAuthTime";
  const SESSION_MS = 30 * 24 * 60 * 60 * 1000;
  const ALLOWED_PASSCODE_HASH = "0f0a1dededa7467d68629e39019182cf6e34c2b09d0f14ee6b98781c7fcd890d";

  function getNextUrl(){
    const params = new URLSearchParams(window.location.search);
    const next = params.get("next");
    if (!next || next.startsWith("http://") || next.startsWith("https://") || next.startsWith("//")) {
      return "index.html";
    }
    return next;
  }

  async function sha256(value){
    const bytes = new TextEncoder().encode(value);
    const digest = await crypto.subtle.digest("SHA-256", bytes);
    return Array.from(new Uint8Array(digest))
      .map(byte => byte.toString(16).padStart(2, "0"))
      .join("");
  }

  function setAuthenticated(){
    localStorage.setItem(AUTH_KEY, "true");
    localStorage.setItem(AUTH_TIME_KEY, String(Date.now()));
  }

  function clearAuthenticated(){
    localStorage.removeItem(AUTH_KEY);
    localStorage.removeItem(AUTH_TIME_KEY);
  }

  function hasValidSession(){
    const isAuthed = localStorage.getItem(AUTH_KEY) === "true";
    const authTime = Number(localStorage.getItem(AUTH_TIME_KEY));
    return isAuthed && authTime && Date.now() - authTime < SESSION_MS;
  }

  document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("authForm");
    const input = document.getElementById("passcode");
    const error = document.getElementById("authError");

    if (hasValidSession()) {
      window.location.replace(getNextUrl());
      return;
    }

    clearAuthenticated();

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      error.textContent = "";

      const passcode = input.value.trim();
      if (!passcode) {
        error.textContent = "アクセスコードを入力してください。";
        input.focus();
        return;
      }

      try {
        const hash = await sha256(passcode);
        if (hash === ALLOWED_PASSCODE_HASH) {
          setAuthenticated();
          window.location.replace(getNextUrl());
          return;
        }
        error.textContent = "アクセスコードが違います。";
        input.select();
      } catch (err) {
        error.textContent = "認証処理に失敗しました。ブラウザを更新して再度お試しください。";
      }
    });
  });
})();
