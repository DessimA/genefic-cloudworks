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
      else this.toast.show('Insira a URL do GitHub para iniciar a narrativa.', 'warning');
    });
  }

  async handleAnalysis(repoUrl) {
    this.toast.show(`Consultando IA GENEFIC...`, 'info');
    this.analyzeBtn.disabled = true;
    this.analyzeBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i>';
    
    try {
      const response = await fetch(CONFIG.API_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: repoUrl })
      });

      const result = await response.json();
      if (!response.ok) throw new Error(result.error || `Erro: ${response.statusText}`);

      // 1. Mostrar área de resultados
      const resultsArea = document.querySelector('#results-area');
      if (resultsArea) resultsArea.style.display = 'block';

      // 2. Preencher Tech Score Gauge
      const scoreVal = result.tech_score || 85;
      const gauge = document.querySelector('#score-gauge');
      if (gauge) {
        gauge.style.setProperty('--score', scoreVal);
        gauge.setAttribute('data-value', scoreVal);
      }

      // 3. Nome do Projeto e Narrativa
      if (document.querySelector('#res-repo-name')) {
        document.querySelector('#res-repo-name').textContent = result.repo_name;
      }
      if (document.querySelector('#ats-result')) {
        document.querySelector('#ats-result').textContent = result.analysis;
      }

      // 4. Tags de Tecnologia (Extração Simulada baseada na IA)
      const stackTagsEl = document.querySelector('#stack-tags');
      if (stackTagsEl) {
        stackTagsEl.innerHTML = `
            <span class="skill-tag">Python</span>
            <span class="skill-tag">Cloud Native</span>
            <span class="skill-tag">REST API</span>
            <span class="skill-tag">AWS Architecture</span>
        `;
      }

      // 5. Sugestões de Evolução
      const suggestions = document.querySelector('#suggestions-list');
      if (suggestions) {
        suggestions.innerHTML = `
            <li><i class="fa-solid fa-check-double" style="color: var(--color-primary)"></i> <strong>Documentação:</strong> Adicione um guia de arquitetura técnica no README.</li>
            <li><i class="fa-solid fa-check-double" style="color: var(--color-primary)"></i> <strong>Qualidade:</strong> Implemente testes unitários para elevar seu Tech Score.</li>
            <li><i class="fa-solid fa-check-double" style="color: var(--color-primary)"></i> <strong>Deploy:</strong> Adicione badges de status de CI/CD para demonstrar maturidade DevOps.</li>
        `;
      }

      this.toast.show(`Análise concluída com sucesso!`, 'success');
      resultsArea.scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
      console.error('Erro:', error);
      this.toast.show(`Falha na análise: ${error.message}`, 'error');
    } finally {
      this.analyzeBtn.disabled = false;
      this.analyzeBtn.innerHTML = '<i class="fa-solid fa-bolt"></i>';
    }
  }
}