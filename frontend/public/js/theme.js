export class ThemeManager {
  constructor() {
    this.storageKey = 'genefic-theme';
    this.theme = localStorage.getItem(this.storageKey) || 'light';
  }

  init() {
    this.applyTheme(this.theme);
    document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
      btn.addEventListener('click', () => this.toggleTheme());
    });
  }

  applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(this.storageKey, theme);
    this.theme = theme;
    
    // Atualiza o ícone em todos os botões de tema
    document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
      const icon = btn.querySelector('i');
      if (icon) {
        icon.className = theme === 'light' ? 'fa-solid fa-moon' : 'fa-solid fa-sun';
      }
    });
    
    // Dispara evento para outros componentes se necessário
    window.dispatchEvent(new CustomEvent('themechanged', { detail: { theme } }));
  }

  toggleTheme() {
    const newTheme = this.theme === 'light' ? 'dark' : 'light';
    this.applyTheme(newTheme);
  }
}
