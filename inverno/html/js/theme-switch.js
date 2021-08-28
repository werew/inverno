
function themeSwitch() {
    var slider = document.getElementById("toggle");
    var themeLight = document.getElementById("theme-link-light");
    var themeDark = document.getElementById("theme-link-dark");
    var themeSet = localStorage.getItem("theme");

    // Get slider click and change theme to dark if current theme is light, otherwise change to light.
    // The switch is done by disabling/enabling the dark theme stylesheet which should be placed after
    // the light theme one. Disabling also the light theme css will leave the page style-less for an 
    // instant (until the css gets parsed) which we should avoid.
    if (slider.checked) {
        themeDark.disabled = false;
        localStorage.setItem("theme", "dark");
    } else {
        themeDark.disabled = true;
        localStorage.setItem("theme", "light");
    }
}

window.onload = (event) => {
    var themeSet = localStorage.getItem("theme");
    var slider = document.getElementById("toggle");
    if (themeSet === "dark"){
        slider.checked = true;
    } else if (themeSet === "light"){
        slider.checked = false;
    }
    themeSwitch();
};


