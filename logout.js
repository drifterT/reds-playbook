(function(){
  "use strict";

  const AUTH_KEY = "redsPlaybookAuth";
  const AUTH_TIME_KEY = "redsPlaybookAuthTime";

  document.addEventListener("DOMContentLoaded", () => {
    const link = document.getElementById("logoutLink");
    if (!link) return;

    link.addEventListener("click", (event) => {
      event.preventDefault();
      localStorage.removeItem(AUTH_KEY);
      localStorage.removeItem(AUTH_TIME_KEY);
      window.location.href = "auth.html";
    });
  });
})();
