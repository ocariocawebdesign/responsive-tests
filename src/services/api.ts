import { AnalysisResult } from '../stores/analysisStore';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiService {
  private logNetworkError(context: string, url: string, error: unknown) {
    const origin = typeof window !== 'undefined' ? window.location.origin : 'unknown';
    const online = typeof navigator !== 'undefined' ? navigator.onLine : true;
    const msg = error instanceof Error ? error.message : String(error);
    console.error(`[Diagnóstico] ${context} falhou`, {
      apiBaseUrl: API_BASE_URL,
      requestUrl: url,
      frontendOrigin: origin,
      online,
      error: msg
    });
  }

  private async diagnose(): Promise<void> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/health`, { method: 'GET' });
      const ok = res.ok;
      console.info('[Diagnóstico] Healthcheck da API', {
        url: `${API_BASE_URL}/api/health`,
        status: res.status,
        ok
      });
    } catch (e) {
      this.logNetworkError('healthcheck', `${API_BASE_URL}/api/health`, e);
    }
  }
  private async fetchWithTimeout(url: string, options: RequestInit = {}, timeout = 30000): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      this.logNetworkError('fetchWithTimeout', url, error);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Tempo limite da requisição excedido');
      }
      throw error;
    }
  }

  async analyzeUrl(url: string): Promise<{ analysis_id: string }> {
    try {
      const response = await this.fetchWithTimeout(`${API_BASE_URL}/api/analyze`, {
        method: 'POST',
        body: JSON.stringify({ url }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Erro desconhecido' }));
        throw new Error(error.error || `Erro ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      this.logNetworkError('analyzeUrl', `${API_BASE_URL}/api/analyze`, error);
      await this.diagnose();
      console.error('Erro ao iniciar análise:', error);
      throw error;
    }
  }

  async getAnalysisStatus(analysisId: string): Promise<AnalysisResult> {
    try {
      const response = await this.fetchWithTimeout(`${API_BASE_URL}/api/analysis/${analysisId}`);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Erro desconhecido' }));
        throw new Error(error.error || `Erro ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erro ao obter status da análise:', error);
      throw error;
    }
  }

  async getScreenshots(analysisId: string): Promise<Blob[]> {
    try {
      const response = await this.fetchWithTimeout(`${API_BASE_URL}/api/screenshots/${analysisId}`);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Erro desconhecido' }));
        throw new Error(error.error || `Erro ${response.status}: ${response.statusText}`);
      }

      // Assume que o backend retorna uma lista de URLs para as imagens
      const screenshotUrls = await response.json();
      
      // Fazer download de cada screenshot
      const screenshotPromises = screenshotUrls.map(async (url: string) => {
        const imageResponse = await fetch(`${API_BASE_URL}${url}`);
        return imageResponse.blob();
      });

      return await Promise.all(screenshotPromises);
    } catch (error) {
      console.error('Erro ao obter screenshots:', error);
      throw error;
    }
  }

  async getHistory(): Promise<AnalysisResult[]> {
    try {
      const response = await this.fetchWithTimeout(`${API_BASE_URL}/api/history`);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Erro desconhecido' }));
        throw new Error(error.error || `Erro ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erro ao obter histórico:', error);
      throw error;
    }
  }

  // Método para polling do status da análise
  async pollAnalysisStatus(
    analysisId: string, 
    onUpdate: (status: AnalysisResult) => void,
    onError: (error: string) => void,
    maxAttempts = 60, // 5 minutos com intervalos de 5 segundos
    interval = 5000
  ): Promise<void> {
    let attempts = 0;

    const poll = async () => {
      try {
        attempts++;
        const status = await this.getAnalysisStatus(analysisId);
        
        onUpdate(status);

        // Se a análise estiver completa ou com erro, parar o polling
        if (status.status === 'completed' || status.status === 'error') {
          return;
        }

        // Se atingiu o máximo de tentativas, parar
        if (attempts >= maxAttempts) {
          onError('Tempo limite excedido. A análise está demorando mais que o esperado.');
          return;
        }

        // Continuar polling
        setTimeout(poll, interval);
      } catch (error) {
        console.error('Erro no polling:', error);
        
        // Se for erro de timeout ou atingiu o máximo de tentativas, parar
        if (attempts >= maxAttempts || error instanceof Error && error.message.includes('timeout')) {
          onError('Erro ao verificar status da análise. Por favor, tente novamente.');
          return;
        }

        // Tentar novamente após um intervalo maior
        setTimeout(poll, interval * 2);
      }
    };

    // Iniciar o polling
    poll();
  }
}

export const apiService = new ApiService();
export default apiService;
