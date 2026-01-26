// frontend/js/auth.js
import { CONFIG } from './config.js';

export class AuthManager {
  static isAuthenticated() {
    return localStorage.getItem('auth_token') !== null;
  }

  static async login(email, password) {
    console.log('Tentando login para:', email);
    // Simulação local - Em produção chamaria a API
    localStorage.setItem('auth_token', 'mock-jwt-token');
    localStorage.setItem('user_email', email);
    window.location.href = 'dashboard.html';
  }

  static mockLogin() {
    localStorage.setItem('auth_token', 'github-mock-token');
    localStorage.setItem('user_email', 'github-user@github.com');
    window.location.href = 'dashboard.html';
  }

  static logout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_email');
    window.location.href = 'index.html';
  }

  static requireAuth() {
    if (!this.isAuthenticated()) {
      window.location.href = 'login.html';
    } else {
        const email = localStorage.getItem('user_email');
        const display = document.getElementById('user-display');
        if (display && email) display.textContent = email.split('@')[0];
    }
  }
}
