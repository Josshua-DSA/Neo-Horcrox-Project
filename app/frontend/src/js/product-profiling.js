document.addEventListener("DOMContentLoaded", () => {
  const shippingButtons = document.querySelectorAll(".tab-btn[data-mode]");

  shippingButtons.forEach((button) => {
    button.type = "button";
    button.setAttribute("aria-pressed", button.classList.contains("active") ? "true" : "false");

    button.addEventListener("click", () => {
      shippingButtons.forEach((item) => {
        const isActive = item === button;
        item.classList.toggle("active", isActive);
        item.setAttribute("aria-pressed", isActive ? "true" : "false");
      });
    });
  });
});
