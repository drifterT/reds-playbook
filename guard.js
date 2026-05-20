(function(){
  "use strict";

  const AUTH_KEY = "redsPlaybookAuth";
  const AUTH_TIME_KEY = "redsPlaybookAuthTime";
  const SESSION_MS = 30 * 24 * 60 * 60 * 1000;

  function pageName(){
    return window.location.pathname.split("/").pop() || "index.html";
  }

  function clearAuth(){
    localStorage.removeItem(AUTH_KEY);
    localStorage.removeItem(AUTH_TIME_KEY);
  }

  function isAuthenticated(){
    try {
      const authed = localStorage.getItem(AUTH_KEY) === "true";
      const authTime = Number(localStorage.getItem(AUTH_TIME_KEY));
      if (!authed || !authTime) return false;
      if (Date.now() - authTime >= SESSION_MS) {
        clearAuth();
        return false;
      }
      return true;
    } catch (err) {
      return false;
    }
  }

  if (!isAuthenticated()) {
    const next = pageName() + window.location.search + window.location.hash;
    window.location.replace("auth.html?next=" + encodeURIComponent(next));
  }
})();
