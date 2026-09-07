// 移动端菜单切换
const menuBtn = document.getElementById('menu-btn');
const mobileMenu = document.getElementById('mobile-menu');
if (menuBtn && mobileMenu) {
  menuBtn.addEventListener('click', () => {
    mobileMenu.classList.toggle('hidden');
  });
  mobileMenu.querySelectorAll('a').forEach((a) => {
    a.addEventListener('click', () => mobileMenu.classList.add('hidden'));
  });
}

// 滚动入场动画
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.12 }
);
document.querySelectorAll('.reveal').forEach((el) => observer.observe(el));

// 登录/注册模式切换
const modeLinks = document.querySelectorAll('[data-mode]');
if (modeLinks.length) {
  modeLinks.forEach((link) => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const mode = link.getAttribute('data-mode');
      const loginForm = document.getElementById('login-form');
      const registerForm = document.getElementById('register-form');
      if (mode === 'register') {
        loginForm.classList.add('hidden');
        registerForm.classList.remove('hidden');
      } else {
        registerForm.classList.add('hidden');
        loginForm.classList.remove('hidden');
      }
      // 切换时清空提示消息
      const msg = document.getElementById('form-msg');
      if (msg) msg.classList.add('hidden');
    });
  });
}