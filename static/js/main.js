// main.js — global utilities

// Navbar transparency on scroll
const navbar = document.getElementById('navbar');
if (navbar) {
  window.addEventListener('scroll', () => {
    navbar.style.background = window.scrollY > 10
      ? 'rgba(8,11,20,0.92)'
      : 'rgba(8,11,20,0.75)';
  }, { passive: true });
}

// Auto-dismiss alerts after 4 s
document.querySelectorAll('.alert').forEach(alert => {
  setTimeout(() => alert.remove(), 4000);
});
