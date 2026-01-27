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
    
    if (document.getElementById('analyze-btn')) {
        this.upload.init();
    }
  }

  initTyped() {
    if (document.getElementById('typed-text')) {
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
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const app = new App();
  app.init();
});
