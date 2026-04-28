const reveals = document.querySelectorAll(".reveal");
const siteHeader = document.querySelector(".site-header");

if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("visible");
                }
            });
        },
        { threshold: 0.15, rootMargin: "0px 0px -50px 0px" },
    );

    reveals.forEach((item) => observer.observe(item));
} else {
    reveals.forEach((item) => item.classList.add("visible"));
}

const toggleHeaderState = () => {
    if (!siteHeader) {
        return;
    }
    if (window.scrollY > 12) {
        siteHeader.classList.add("scrolled");
    } else {
        siteHeader.classList.remove("scrolled");
    }
};

window.addEventListener("scroll", toggleHeaderState);
window.addEventListener("load", toggleHeaderState);

const progressSliders = document.querySelectorAll(".progress-slider");
progressSliders.forEach((slider) => {
    const targetId = slider.dataset.target;
    const output = targetId ? document.getElementById(targetId) : null;

    const renderValue = () => {
        if (output) {
            output.textContent = `${slider.value}%`;
        }
    };

    slider.addEventListener("input", renderValue);
    renderValue();
});
