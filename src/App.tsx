import React, { useState, useEffect } from 'react';
import { useAnalysisStore } from './stores/analysisStore';
import type { AnalysisResult } from './stores/analysisStore';
import { apiService } from './services/api';
import UrlInput from './components/UrlInput';
import LoadingState from './components/LoadingState';
import Screenshots from './components/Screenshots';
import Diagnosis from './components/Diagnosis';
import Report from './components/Report';
import { History, RefreshCw, ExternalLink } from 'lucide-react';

function App() {
  const { 
    currentAnalysis, 
    isLoading, 
    startAnalysis, 
    updateAnalysisStatus, 
    completeAnalysis, 
    setError, 
    clearCurrentAnalysis 
  } = useAnalysisStore();

  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState<AnalysisResult[]>([]);

  useEffect(() => {
    // Load history from localStorage on mount
    const savedHistory = localStorage.getItem('analysisHistory');
    if (savedHistory) {
      setHistory(JSON.parse(savedHistory));
    }
  }, []);

  useEffect(() => {
    // Save history to localStorage when it changes
    localStorage.setItem('analysisHistory', JSON.stringify(history));
  }, [history]);

  const handleAnalyze = async (url: string) => {
    try {
      startAnalysis(url);
      
      // Iniciar análise no backend
      const { analysis_id } = await apiService.analyzeUrl(url);
      
      // Atualizar status para analisando
      updateAnalysisStatus({
        status: 'analyzing',
        currentStep: 1,
        statusMessage: 'Capturando screenshots...'
      });

      // Iniciar polling do status
      apiService.pollAnalysisStatus(
        analysis_id,
        (status) => {
          updateAnalysisStatus(status);
        },
        (error) => {
          setError(error);
        }
      );

    } catch (error) {
      console.error('Erro ao iniciar análise:', error);
      setError(error instanceof Error ? error.message : 'Erro desconhecido');
    }
  };

  const handleNewAnalysis = () => {
    clearCurrentAnalysis();
  };

  const handleViewHistory = () => {
    setShowHistory(!showHistory);
  };

  const handleLoadFromHistory = (analysis: AnalysisResult) => {
    completeAnalysis(analysis);
    setShowHistory(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="bg-blue-600 text-white p-2 rounded-lg">
                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Teste Responsivo com IA</h1>
                <p className="text-sm text-gray-600">Análise inteligente de responsividade web</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <button
                onClick={handleViewHistory}
                className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <History className="h-4 w-4" />
                <span className="hidden sm:inline">Histórico</span>
              </button>
              
              {currentAnalysis && (
                <button
                  onClick={handleNewAnalysis}
                  className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <RefreshCw className="h-4 w-4" />
                  <span className="hidden sm:inline">Nova Análise</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* History Modal */}
      {showHistory && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-96 overflow-hidden">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Histórico de Análises</h3>
                <button
                  onClick={() => setShowHistory(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
            </div>
            <div className="p-4 overflow-y-auto max-h-80">
              {history.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  <History className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Nenhuma análise no histórico</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {history.map((item) => (
                    <div
                      key={item.id}
                      className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                      onClick={() => handleLoadFromHistory(item)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {item.url}
                          </p>
                          <p className="text-xs text-gray-500">
                            {new Date().toLocaleString('pt-BR')}
                          </p>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            item.status === 'completed' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {item.status === 'completed' ? 'Concluído' : 'Erro'}
                          </span>
                          <ExternalLink className="h-4 w-4 text-gray-400" />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!currentAnalysis ? (
          // Initial State
          <div className="text-center">
            <div className="max-w-3xl mx-auto">
              <div className="bg-white rounded-lg shadow-sm border p-8 mb-8">
                <div className="mb-6">
                  <div className="bg-blue-100 text-blue-600 p-4 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                    <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    Teste a Responsividade do Seu Site
                  </h2>
                  <p className="text-gray-600 mb-6">
                    Insira a URL do seu site e nossa IA analisará a responsividade em diferentes dispositivos, 
                    identificando problemas e fornecendo recomendações práticas.
                  </p>
                </div>
                
                <UrlInput onSubmit={handleAnalyze} isLoading={isLoading} />
              </div>

              {/* Features */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white rounded-lg shadow-sm border p-6">
                  <div className="bg-green-100 text-green-600 p-3 rounded-lg w-12 h-12 mb-4 flex items-center justify-center">
                    <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4V2a1 1 0 018 0v2m0 0V2a1 1 0 018 0v2m-9 8h10M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Análise Multi-Dispositivo</h3>
                  <p className="text-gray-600 text-sm">
                    Teste em mobile, tablet, desktop e 4K com capturas de tela detalhadas.
                  </p>
                </div>

                <div className="bg-white rounded-lg shadow-sm border p-6">
                  <div className="bg-blue-100 text-blue-600 p-3 rounded-lg w-12 h-12 mb-4 flex items-center justify-center">
                    <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">IA Inteligente</h3>
                  <p className="text-gray-600 text-sm">
                    Detecção automática de problemas com sugestões práticas e exemplos de código.
                  </p>
                </div>

                <div className="bg-white rounded-lg shadow-sm border p-6">
                  <div className="bg-purple-100 text-purple-600 p-3 rounded-lg w-12 h-12 mb-4 flex items-center justify-center">
                    <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Relatórios Detalhados</h3>
                  <p className="text-gray-600 text-sm">
                    Gere relatórios completos em HTML com recomendações e exemplos de código.
                  </p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          // Analysis Results
          <div className="space-y-8">
            {/* Status and Controls */}
            {currentAnalysis.status === 'analyzing' && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <LoadingState 
                  status={currentAnalysis.statusMessage || 'Analisando...'}
                  currentStep={currentAnalysis.currentStep || 1}
                  totalSteps={currentAnalysis.totalSteps || 4}
                />
              </div>
            )}

            {currentAnalysis.status === 'error' && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                <div className="flex items-center space-x-3">
                  <div className="bg-red-100 text-red-600 p-2 rounded-full">
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-red-900">Erro na Análise</h3>
                    <p className="text-red-700">{currentAnalysis.error}</p>
                  </div>
                </div>
                
                <div className="mt-4 flex space-x-3">
                  <button
                    onClick={handleNewAnalysis}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                  >
                    Tentar Novamente
                  </button>
                </div>
              </div>
            )}

            {currentAnalysis.status === 'completed' && (
              <>
                {/* Screenshots */}
                {currentAnalysis.screenshots.length > 0 && (
                  <Screenshots 
                    screenshots={currentAnalysis.screenshots} 
                    analysisId={currentAnalysis.id}
                  />
                )}

                {/* Diagnosis */}
                {currentAnalysis.issues.length > 0 && (
                  <Diagnosis issues={currentAnalysis.issues} />
                )}

                {/* Report */}
                {currentAnalysis.recommendations.length > 0 && (
                  <Report 
                    report={{
                      id: currentAnalysis.id,
                      url: currentAnalysis.url,
                      timestamp: new Date().toISOString(),
                      summary: currentAnalysis.summary,
                      recommendations: currentAnalysis.recommendations,
                      score: currentAnalysis.score
                    }}
                  />
                )}

                {/* Summary Card */}
                <div className="bg-white rounded-lg shadow-sm border p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">Resumo da Análise</h3>
                    <div className="flex items-center space-x-2">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                        currentAnalysis.score.overall >= 80 
                          ? 'bg-green-100 text-green-800'
                          : currentAnalysis.score.overall >= 60
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        Score: {currentAnalysis.score.overall}/100
                      </span>
                    </div>
                  </div>
                  
                  <p className="text-gray-700 mb-4">
                    {currentAnalysis.summary || 'Análise concluída com sucesso. Verifique os problemas detectados e as recomendações fornecidas.'}
                  </p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Screenshots:</span>
                      <span className="font-medium">{currentAnalysis.screenshots.length}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Problemas:</span>
                      <span className="font-medium">{currentAnalysis.issues.length}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Recomendações:</span>
                      <span className="font-medium">{currentAnalysis.recommendations.length}</span>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
