import { create } from 'zustand';

interface ScreenshotData {
  id: string;
  device: string;
  resolution: string;
  url: string;
  fullPageUrl?: string;
}

interface Issue {
  id: string;
  type: 'critical' | 'warning' | 'info';
  severity: number;
  title: string;
  description: string;
  device: 'mobile' | 'tablet' | 'desktop' | '4k';
  element?: string;
  suggestion?: string;
}

interface Recommendation {
  id: string;
  category: 'css' | 'html' | 'accessibility' | 'performance' | 'ux';
  title: string;
  description: string;
  codeExample?: string;
  before?: string;
  after?: string;
  documentation?: string;
  priority: 'high' | 'medium' | 'low';
}

export interface AnalysisResult {
  id: string;
  url: string;
  status: 'pending' | 'analyzing' | 'completed' | 'error';
  screenshots: ScreenshotData[];
  issues: Issue[];
  recommendations: Recommendation[];
  summary: string;
  score: {
    mobile: number;
    tablet: number;
    desktop: number;
    overall: number;
  };
  error?: string;
  currentStep?: number;
  totalSteps?: number;
  statusMessage?: string;
}

interface AnalysisStore {
  currentAnalysis: AnalysisResult | null;
  history: AnalysisResult[];
  isLoading: boolean;
  
  // Actions
  startAnalysis: (url: string) => void;
  updateAnalysisStatus: (status: Partial<AnalysisResult>) => void;
  completeAnalysis: (result: AnalysisResult) => void;
  setError: (error: string) => void;
  addToHistory: (analysis: AnalysisResult) => void;
  clearCurrentAnalysis: () => void;
  loadAnalysisFromHistory: (id: string) => void;
}

export const useAnalysisStore = create<AnalysisStore>((set, get) => ({
  currentAnalysis: null,
  history: [],
  isLoading: false,

  startAnalysis: (url: string) => {
    const newAnalysis: AnalysisResult = {
      id: Date.now().toString(),
      url,
      status: 'pending',
      screenshots: [],
      issues: [],
      recommendations: [],
      summary: '',
      score: {
        mobile: 0,
        tablet: 0,
        desktop: 0,
        overall: 0
      },
      currentStep: 1,
      totalSteps: 4,
      statusMessage: 'Iniciando análise...'
    };

    set({
      currentAnalysis: newAnalysis,
      isLoading: true
    });
  },

  updateAnalysisStatus: (statusUpdate: Partial<AnalysisResult>) => {
    const { currentAnalysis } = get();
    if (currentAnalysis) {
      set({
        currentAnalysis: {
          ...currentAnalysis,
          ...statusUpdate
        }
      });
    }
  },

  completeAnalysis: (result: AnalysisResult) => {
    set({
      currentAnalysis: result,
      isLoading: false
    });
    
    // Add to history
    get().addToHistory(result);
  },

  setError: (error: string) => {
    const { currentAnalysis } = get();
    if (currentAnalysis) {
      set({
        currentAnalysis: {
          ...currentAnalysis,
          status: 'error',
          error,
        },
        isLoading: false
      });
    }
  },

  addToHistory: (analysis: AnalysisResult) => {
    const { history } = get();
    const newHistory = [analysis, ...history].slice(0, 10); // Keep only last 10 analyses
    set({ history: newHistory });
  },

  clearCurrentAnalysis: () => {
    set({
      currentAnalysis: null,
      isLoading: false
    });
  },

  loadAnalysisFromHistory: (id: string) => {
    const { history } = get();
    const analysis = history.find(item => item.id === id);
    if (analysis) {
      set({
        currentAnalysis: analysis,
        isLoading: false
      });
    }
  }
}));
