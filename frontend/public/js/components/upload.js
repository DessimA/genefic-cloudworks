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
    this.toast.show(`Iniciando Análise Estratégica...`, 'info');
    this.analyzeBtn.disabled = true;
    this.analyzeBtn.innerHTML = '<i class="fa-solid fa-brain fa-fade"></i>';
    const loadingIndicator = document.querySelector('#loading-indicator');
    if (loadingIndicator) loadingIndicator.style.display = 'block';
    
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
          if (loadingIndicator) loadingIndicator.style.display = 'none';
          this.toast.show(`Erro na Análise: ${e.message}`, 'error');
          this.resetButton();
        }
      }, 3000);

    } catch (error) {
      if (loadingIndicator) loadingIndicator.style.display = 'none';
      this.toast.show(`Falha na Conexão: ${error.message}`, 'error');
      this.resetButton();
    }
  }

  renderResults(result) {
    const data = result.structured_data;
    document.querySelector('#results-area').style.display = 'block';
    document.querySelector('#res-repo-name').textContent = result.repo_url.split('/').pop();

    // Atualizar Score e Gauge
    const scoreVal = document.querySelector('#tech-score-val');
    const gaugePath = document.querySelector('#gauge-path');
    
    if (scoreVal) scoreVal.textContent = data.tech_score;
    if (gaugePath) {
      gaugePath.style.strokeDasharray = `${data.tech_score}, 100`;
    }

    document.querySelector('#ats-result').innerHTML = `
      <div class="glass-panel" style="padding: 24px; border-left: 4px solid var(--color-primary); position: relative;">
          <button class="btn btn--ghost btn--sm" style="position: absolute; top: 16px; right: 16px;" onclick="navigator.clipboard.writeText(\`${data.ats_summary}\`).then(() => alert('Copiado!'))" title="Copiar"><i class="fa-solid fa-copy"></i></button>
          <h4 style="font-weight: 800; margin-bottom: 12px;"><i class="fa-solid fa-file-lines"></i> Narrativa Profissional (ATS)</h4>
          <p style="font-size: 0.95rem; line-height: 1.6; font-style: italic;">"${data.ats_summary}"</p>
      </div>

      <div class="glass-panel" style="padding: 24px; border-left: 4px solid var(--color-accent);">
          <h4 style="font-weight: 800; margin-bottom: 12px;"><i class="fa-solid fa-award"></i> Conquistas Técnicas</h4>
          <ul style="font-size: 0.9rem; padding-left: 20px; line-height: 1.6;">
            ${(data.key_achievements || []).map(a => `<li>${a}</li>`).join('')}
          </ul>
      </div>
      
      <div class="glass-panel" style="padding: 24px; border-left: 4px solid var(--color-secondary);">
          <h4 style="font-weight: 800; margin-bottom: 12px;"><i class="fa-solid fa-lightbulb"></i> Sugestões de Melhoria</h4>
          <ul style="font-size: 0.9rem; padding-left: 20px; line-height: 1.6;">
            ${(data.improvements || []).map(i => `<li>${i}</li>`).join('')}
          </ul>
      </div>
    `;

    const stackTagsEl = document.querySelector('#stack-tags');
    if (stackTagsEl) {
      stackTagsEl.innerHTML = (data.technologies || []).map(t => `<span class="skill-tag">${t}</span>`).join('');
    }

    this.toast.show(`Análise Concluída!`, 'success');
    document.querySelector('#results-area').scrollIntoView({ behavior: 'smooth' });
    this.resetButton();
  }

  resetButton() {
    this.analyzeBtn.disabled = false;
    this.analyzeBtn.innerHTML = '<i class="fa-solid fa-bolt"></i>';
  }
}
