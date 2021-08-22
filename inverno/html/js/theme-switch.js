function themeSwitch() {
var slider = document.getElementById("toggle");
var theme = document.getElementById("theme-link");

// Get slider click and change theme to dark if current theme is light, otherwise change to light
if (slider.checked == true) {
    theme.href = "css/sb-admin-2-dark.css";
  } else {
    theme.href = "css/sb-admin-2.css";
  }
}