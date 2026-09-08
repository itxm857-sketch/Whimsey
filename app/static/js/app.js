document.addEventListener('DOMContentLoaded', () => {
  const menuToggle = document.querySelector('[data-menu-toggle]');
  const menu = document.querySelector('[data-mobile-menu]');
  if (menuToggle && menu) menuToggle.addEventListener('click', () => menu.classList.toggle('open'));

  document.querySelectorAll('[data-confirm]').forEach(form => {
    form.addEventListener('submit', e => {
      if (!window.confirm(form.dataset.confirm)) e.preventDefault();
    });
  });

  document.querySelectorAll('.qty-control').forEach(control => {
    const input = control.querySelector('input');
    const minus = control.querySelector('[data-qty-minus]');
    const plus = control.querySelector('[data-qty-plus]');
    if (!input) return;
    const sync = () => {
      const min = Number(input.min || 1), max = Number(input.max || 9999);
      let value = Number(input.value || min);
      value = Math.max(min, Math.min(max, value));
      input.value = value;
    };
    minus?.addEventListener('click', () => { input.value = Number(input.value || 1) - 1; sync(); });
    plus?.addEventListener('click', () => { input.value = Number(input.value || 1) + 1; sync(); });
    input.addEventListener('change', sync);
  });

  setTimeout(() => document.querySelectorAll('.flash').forEach(el => el.classList.add('fade')), 5000);
});

  document.querySelectorAll('[data-gallery-image]').forEach(button => button.addEventListener('click', () => { const main=document.querySelector('#mainProductImage'); if(main) main.src=button.dataset.galleryImage; }));
