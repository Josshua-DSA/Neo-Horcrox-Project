const hiddenClass = "native-select-hidden";
const wrapperClass = "glass-select";

export function enhanceGlassSelect(select) {
  if (!select) return null;

  let wrapper = select._glassSelectWrapper;
  if (!wrapper) {
    wrapper = createWrapper();
    select.classList.add(hiddenClass);
    select.insertAdjacentElement("afterend", wrapper);
    select._glassSelectWrapper = wrapper;

    wrapper.querySelector(".glass-select__button").addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      toggleSelect(wrapper);
    });

    select.addEventListener("change", () => refreshGlassSelect(select));
    document.addEventListener("click", (event) => {
      if (!wrapper.contains(event.target)) closeSelect(wrapper);
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeSelect(wrapper);
    });
  }

  refreshGlassSelect(select);
  return wrapper;
}

export function refreshGlassSelect(select) {
  const wrapper = select?._glassSelectWrapper;
  if (!select || !wrapper) return;

  const button = wrapper.querySelector(".glass-select__button");
  const label = wrapper.querySelector(".glass-select__label");
  const menu = wrapper.querySelector(".glass-select__menu");
  const selected = select.selectedOptions[0] || select.options[0];

  label.textContent = selected?.textContent || "Select";
  button.disabled = select.disabled;
  menu.replaceChildren();

  Array.from(select.options).forEach((option) => {
    const item = document.createElement("button");
    item.type = "button";
    item.className = "glass-select__option";
    item.textContent = option.textContent;
    item.dataset.value = option.value;
    item.disabled = option.disabled;
    item.setAttribute("role", "option");
    item.setAttribute("aria-selected", String(option.selected));
    item.classList.toggle("is-selected", option.selected);
    item.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      select.value = option.value;
      select.dispatchEvent(new Event("change", { bubbles: true }));
      closeSelect(wrapper);
    });
    menu.appendChild(item);
  });
}

function createWrapper() {
  const wrapper = document.createElement("div");
  wrapper.className = wrapperClass;
  wrapper.innerHTML = `
    <button class="glass-select__button" type="button" aria-haspopup="listbox" aria-expanded="false">
      <span class="glass-select__label"></span>
      <span class="glass-select__arrow">v</span>
    </button>
    <div class="glass-select__menu" role="listbox"></div>
  `;
  return wrapper;
}

function toggleSelect(wrapper) {
  const isOpen = wrapper.classList.contains("is-open");
  document.querySelectorAll(`.${wrapperClass}.is-open`).forEach(closeSelect);
  if (!isOpen) openSelect(wrapper);
}

function openSelect(wrapper) {
  wrapper.classList.add("is-open");
  wrapper.querySelector(".glass-select__button").setAttribute("aria-expanded", "true");
}

function closeSelect(wrapper) {
  wrapper.classList.remove("is-open");
  wrapper.querySelector(".glass-select__button")?.setAttribute("aria-expanded", "false");
}
