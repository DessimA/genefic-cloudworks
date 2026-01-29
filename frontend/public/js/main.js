import { ThemeManager } from './theme.js';
import { ToastManager } from './components/toast.js';
import { UploadManager } from './components/upload.js';
import { renderTeam } from './components/team.js';

class App {
  constructor() {
    this.theme = new ThemeManager();
    this.toast = new ToastManager();
    this.upload = new UploadManager(this.toast);
  }

  init() {
    this.theme.init();
    renderTeam();
    this.initTyped();
    this.initMobileMenu();
    this.initBackToTop();
    
    if (document.getElementById('analyze-btn')) {
        this.upload.init();
    }
  }

  initBackToTop() {
    const btn = document.getElementById('back-to-top');
    if (!btn) return;

    let ticking = false;

    const updateButton = () => {
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      
      if (scrollTop > 300) {
        btn.classList.add('visible');
      } else {
        btn.classList.remove('visible');
        // Remove o foco se o botão for escondido enquanto focado
        if (document.activeElement === btn) {
          btn.blur();
        }
      }
      
      ticking = false;
    };

    const requestTick = () => {
      if (!ticking) {
        window.requestAnimationFrame(updateButton);
        ticking = true;
      }
    };

    window.addEventListener('scroll', requestTick, { passive: true });
    
    btn.addEventListener('click', () => {
      window.scrollTo({ 
        top: 0, 
        behavior: 'smooth' 
      });
    });
  }

  initMobileMenu() {
    const toggle = document.querySelector('.mobile-menu-toggle');
    const close = document.querySelector('.mobile-menu-close');
    const overlay = document.querySelector('.mobile-menu-overlay');
    const menuContent = document.querySelector('.mobile-menu-content');

    const openMenu = () => {
      overlay.classList.add('active');
      document.body.style.overflow = 'hidden';
    };

    const closeMenu = () => {
      overlay.classList.remove('active');
      document.body.style.overflow = '';
    };

    if (toggle) toggle.addEventListener('click', openMenu);
    if (close) close.addEventListener('click', closeMenu);

    // Close on overlay click (but not on menu content)
    overlay?.addEventListener('click', (e) => {
      if (e.target === overlay) closeMenu();
    });

    // Close on link click
    overlay?.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', closeMenu);
    });
  }

  initTyped() {
    if (document.getElementById('typed-text') && typeof Typed !== 'undefined') {
      try {
        new Typed('#typed-text', {
          strings: [
            'The Minds Behind GENEFIC',
            'Cloud Solutions Experts',
            'AI-Powered Career Growth',
            'Built by Group 3'
          ],
          typeSpeed: 50,
          backSpeed: 30,
          backDelay: 2000,
          loop: true,
          showCursor: true,
          cursorChar: '|'
        });
      } catch (e) {
        console.error("Erro ao inicializar Typed.js:", e);
      }
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const app = new App();
  app.init();
});
