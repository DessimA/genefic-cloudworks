import { CONFIG } from '../config.js';

export class UploadManager {
  constructor(toast) {
    this.toast = toast;
    this.analyzeBtn = null;
    this.urlInput = null;
  }

  init() {
    this.analyzeBtn = document.querySelector('#analyze-btn');
    this.urlInput = document.querySelector('#repo-url');
    if (!this.analyzeBtn || !this.urlInput) return;
    this.setupListeners();
  }

  setupListeners() {
    this.analyzeBtn.addEventListener('click', () => {
      const url = this.urlInput.value;
      if (url) this.handleAnalysis(url);
      else this.toast.show('Insira a URL do GitHub.', 'warning');
    });
  }

  async handleAnalysis(repoUrl) {
    // UI States
    this.analyzeBtn.disabled = true;
    this.analyzeBtn.innerHTML = '<i class="fa-solid fa-brain fa-fade"></i>';
    
    const loadingIndicator = document.querySelector('#loading-indicator');
    const emptyState = document.querySelector('#empty-state');
    const resultsArea = document.querySelector('#results-area');
    const loadingMsg = document.querySelector('#loading-msg');
    
    if (loadingIndicator) loadingIndicator.style.display = 'block';
    if (emptyState) emptyState.style.display = 'none';
    if (resultsArea) resultsArea.style.display = 'none';

    // Dynamic Messages
    const messages = [
      "Clonando metadados do GitHub...",
      "Extraindo tecnologias do README...",
      "Consultando especialistas em IA...",
      "Calculando Tech Authority Score...",
      "Otimizando narrativa para ATS...",
      "Finalizando relatório de impacto..."
    ];
    let msgIndex = 0;
    const msgInterval = setInterval(() => {
      if (loadingMsg) loadingMsg.textContent = messages[msgIndex % messages.length];
      msgIndex++;
    }, 3000);
    
    try {
      // 1. Iniciar Task
      const initRes = await fetch(CONFIG.API_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: repoUrl })
      });
      
      if (!initRes.ok) {
        const errData = await initRes.json();
        throw new Error(errData.error || `Erro no servidor: ${initRes.status}`);
      }
      
      const { task_id } = await initRes.json();

      // 2. Loop de Polling
      const poll = async () => {
        try {
          const statusRes = await fetch(`${CONFIG.API_ENDPOINT}?task_id=${task_id}`);
          if (!statusRes.ok) return false;
          
          const result = await statusRes.json();

          if (result.status === 'COMPLETED') {
            clearInterval(msgInterval);
            this.renderResults(result);
            return true;
          } else if (result.status === 'FAILED') {
            throw new Error(result.structured_data?.error || 'Falha no processamento da IA');
          }
          return false;
        } catch (e) {
          throw e;
        }
      };

      const interval = setInterval(async () => {
        try {
          if (await poll()) {
            clearInterval(interval);
            if (loadingIndicator) loadingIndicator.style.display = 'none';
          }
        } catch (e) {
          clearInterval(interval);
          clearInterval(msgInterval);
          if (loadingIndicator) loadingIndicator.style.display = 'none';
          if (emptyState) emptyState.style.display = 'block';
          this.toast.show(`Erro na Análise: ${e.message}`, 'error');
          this.resetButton();
        }
      }, 3000);

    } catch (error) {
      clearInterval(msgInterval);
      if (loadingIndicator) loadingIndicator.style.display = 'none';
      if (emptyState) emptyState.style.display = 'block';
      this.toast.show(`Falha na Conexão: ${error.message}`, 'error');
      this.resetButton();
    }
  }

  renderResults(result) {
    const data = result.structured_data;
    const resultsArea = document.querySelector('#results-area');
    const emptyState = document.querySelector('#empty-state');
    
    if (resultsArea) resultsArea.style.display = 'block';
    if (emptyState) emptyState.style.display = 'none';

    // Atualizar Score e Gauge
    const scoreVal = document.querySelector('#tech-score-val');
    const gaugePath = document.querySelector('#gauge-path');
    
    if (scoreVal) scoreVal.textContent = data.tech_score;
    if (gaugePath) {
      gaugePath.style.strokeDasharray = `${data.tech_score}, 100`;
    }

    document.querySelector('#ats-result').innerHTML = `
      <div class="dashboard-card" style="border-left: 4px solid var(--color-primary); position: relative;">
          <button class="btn btn--ghost btn--sm btn-copy" style="position: absolute; top: 16px; right: 16px;" title="Copiar"><i class="fa-solid fa-copy"></i></button>
          <h4 style="font-weight: 800; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
            <i class="fa-solid fa-wand-magic-sparkles" style="color: var(--color-primary);"></i> Narrativa Profissional (ATS)
          </h4>
          <p style="font-size: 1rem; line-height: 1.7; color: var(--color-text-primary); font-style: italic;">"${data.ats_summary}"</p>
      </div>

      <div class="dashboard-card" style="border-left: 4px solid var(--color-secondary);">
          <h4 style="font-weight: 800; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
            <i class="fa-solid fa-trophy" style="color: var(--color-secondary);"></i> Conquistas Técnicas
          </h4>
          <ul style="display: grid; gap: 12px; padding: 0; list-style: none;">
            ${(data.key_achievements || []).map(a => `
              <li style="display: flex; gap: 12px; align-items: start; font-size: 0.95rem;">
                <i class="fa-solid fa-check-circle" style="color: var(--color-secondary); margin-top: 4px;"></i>
                <span>${a}</span>
              </li>
            `).join('')}
          </ul>
      </div>
      
      <div class="dashboard-card" style="border-left: 4px solid var(--color-accent);">
          <h4 style="font-weight: 800; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
            <i class="fa-solid fa-lightbulb" style="color: var(--color-accent);"></i> Sugestões de Melhoria
          </h4>
          <ul style="display: grid; gap: 12px; padding: 0; list-style: none;">
            ${(data.improvements || []).map(i => `
              <li style="display: flex; gap: 12px; align-items: start; font-size: 0.95rem;">
                <i class="fa-solid fa-circle-arrow-up" style="color: var(--color-accent); margin-top: 4px;"></i>
                <span>${i}</span>
              </li>
            `).join('')}
          </ul>
      </div>
    `;

    // Configurar botão de cópia após a injeção do HTML
    const copyBtn = document.querySelector('.btn-copy');
    if (copyBtn) {
      copyBtn.addEventListener('click', () => this.copyToClipboard(data.ats_summary));
    }

    const stackTagsEl = document.querySelector('#stack-tags');
    if (stackTagsEl) {
      stackTagsEl.innerHTML = (data.technologies || []).map(t => `
        <span style="background: var(--color-primary-light); color: var(--color-primary); padding: 4px 12px; border-radius: 100px; font-size: 0.75rem; font-weight: 700; border: 1px solid var(--color-primary);">
          ${t}
        </span>
      `).join('');
    }

    this.toast.show(`Análise Concluída!`, 'success');
    if (resultsArea) resultsArea.scrollIntoView({ behavior: 'smooth' });
    this.resetButton();
  }

  async copyToClipboard(text) {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        textArea.style.left = "-9999px";
        textArea.style.top = "-9999px";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand('copy');
        textArea.remove();
      }
      this.toast.show('Copiado para a área de transferência!', 'success');
    } catch (err) {
      this.toast.show('Falha ao copiar texto.', 'error');
    }
  }

  resetButton() {
    this.analyzeBtn.disabled = false;
    this.analyzeBtn.innerHTML = '<i class="fa-solid fa-bolt"></i> ANALISAR';
  }
}