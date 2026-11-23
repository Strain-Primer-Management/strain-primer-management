// Login page: disable the button after the first submit, so a double click cannot send the
// form twice. Plain JavaScript; without it the form still works.
const form = document.getElementById("login-form");
const button = form.querySelector("button[type='submit']");

form.addEventListener("submit", () => {
  button.disabled = true;
  button.textContent = "Logging in…";
});

// Coming back with the browser's Back button must not leave the button disabled.
window.addEventListener("pageshow", (event) => {
  if (event.persisted) {
    button.disabled = false;
    button.textContent = "Log in";
  }
});
