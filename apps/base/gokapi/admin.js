// Seed preferences once per browser; users can choose other expiry values.
(() => {
  if (localStorage.getItem("defaultExpiry") === null) {
    localStorage.setItem("defaultExpiry", "1");
    localStorage.setItem("defaultUnlimitedTime", "false");
  }
  if (localStorage.getItem("defaultUnlimitedDownloads") === null) {
    localStorage.setItem("defaultUnlimitedDownloads", "true");
  }
  if (typeof setUploadDefaults === "function" && document.getElementById("expiryDays")) {
    setUploadDefaults();
  }
})();
