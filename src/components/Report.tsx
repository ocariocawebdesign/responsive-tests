import React, { useState } from 'react';
import { FileText, Download, Copy, Check, ExternalLink, Code, Eye, BookOpen } from 'lucide-react';

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

interface ReportData {
  id: string;
  url: string;
  timestamp: string;
  summary: string;
  recommendations: Recommendation[];
  score: {
    mobile: number;
    tablet: number;
    desktop: number;
    overall: number;
  };
}

interface ReportProps {
  report: ReportData;
}

const Report: React.FC<ReportProps> = ({ report }) => {
  const [copiedCode, setCopiedCode] = useState<string | null>(null);
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [filterPriority, setFilterPriority] = useState<string>('all');

  const categoryIcons = {
    css: Code,
    html: Code,
    accessibility: Eye,
    performance: FileText,
    ux: BookOpen
  };

  const categoryColors = {
    css: 'bg-blue-100 text-blue-800',
    html: 'bg-orange-100 text-orange-800',
    accessibility: 'bg-green-100 text-green-800',
    performance: 'bg-purple-100 text-purple-800',
    ux: 'bg-pink-100 text-pink-800'
  };

  const priorityColors = {
    high: 'bg-red-100 text-red-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-green-100 text-green-800'
  };

  const copyCode = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(id);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const downloadReport = () => {
    const htmlContent = generateHTMLReport(report);
    const blob = new Blob([htmlContent], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `relatorio-responsivo-${report.id}.html`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const filteredRecommendations = report.recommendations.filter(rec => {
    const categoryMatch = filterCategory === 'all' || rec.category === filterCategory;
    const priorityMatch = filterPriority === 'all' || rec.priority === filterPriority;
    return categoryMatch && priorityMatch;
  });

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Relatório de Análise</h3>
            <p className="text-sm text-gray-600">
              Análise completa de responsividade para {report.url}
            </p>
          </div>
          
          <button
            onClick={downloadReport}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Download className="h-4 w-4" />
            <span>Baixar Relatório</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className={`p-4 rounded-lg ${getScoreBgColor(report.score.mobile)}`}>
            <div className="text-center">
              <div className={`text-2xl font-bold ${getScoreColor(report.score.mobile)}`}>
                {report.score.mobile}
              </div>
              <div className="text-sm text-gray-600">Mobile</div>
            </div>
          </div>
          
          <div className={`p-4 rounded-lg ${getScoreBgColor(report.score.tablet)}`}>
            <div className="text-center">
              <div className={`text-2xl font-bold ${getScoreColor(report.score.tablet)}`}>
                {report.score.tablet}
              </div>
              <div className="text-sm text-gray-600">Tablet</div>
            </div>
          </div>
          
          <div className={`p-4 rounded-lg ${getScoreBgColor(report.score.desktop)}`}>
            <div className="text-center">
              <div className={`text-2xl font-bold ${getScoreColor(report.score.desktop)}`}>
                {report.score.desktop}
              </div>
              <div className="text-sm text-gray-600">Desktop</div>
            </div>
          </div>
          
          <div className={`p-4 rounded-lg bg-gray-100`}>
            <div className="text-center">
              <div className={`text-2xl font-bold ${getScoreColor(report.score.overall)}`}>
                {report.score.overall}
              </div>
              <div className="text-sm text-gray-600">Geral</div>
            </div>
          </div>
        </div>

        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Sumário Executivo</h4>
          <p className="text-sm text-gray-700 bg-gray-50 p-4 rounded-lg">
            {report.summary}
          </p>
        </div>

        <div className="flex flex-wrap gap-4">
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">Categoria:</label>
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Todas</option>
              <option value="css">CSS</option>
              <option value="html">HTML</option>
              <option value="accessibility">Acessibilidade</option>
              <option value="performance">Performance</option>
              <option value="ux">UX</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">Prioridade:</label>
            <select
              value={filterPriority}
              onChange={(e) => setFilterPriority(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Todas</option>
              <option value="high">Alta</option>
              <option value="medium">Média</option>
              <option value="low">Baixa</option>
            </select>
          </div>
        </div>
      </div>

      <div className="divide-y divide-gray-200">
        {filteredRecommendations.map((recommendation) => {
          const IconComponent = categoryIcons[recommendation.category];
          const categoryColor = categoryColors[recommendation.category];
          const priorityColor = priorityColors[recommendation.priority];

          return (
            <div key={recommendation.id} className="p-6">
              <div className="flex items-start space-x-3">
                <div className={`p-2 rounded-lg ${categoryColor}`}>
                  <IconComponent className="h-5 w-5" />
                </div>
                
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-lg font-medium text-gray-900">
                      {recommendation.title}
                    </h4>
                    
                    <div className="flex items-center space-x-2">
                      <div className={`px-2 py-1 rounded-full text-xs font-medium ${categoryColor}`}>
                        {recommendation.category.toUpperCase()}
                      </div>
                      
                      <div className={`px-2 py-1 rounded-full text-xs font-medium ${priorityColor}`}>
                        {recommendation.priority.toUpperCase()}
                      </div>
                    </div>
                  </div>

                  <p className="text-gray-700 mb-4">
                    {recommendation.description}
                  </p>

                  {recommendation.before && recommendation.after && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      <div>
                        <h5 className="text-sm font-medium text-gray-900 mb-2">Antes:</h5>
                        <div className="bg-red-50 border border-red-200 rounded-md p-3">
                          <code className="text-sm text-red-800">{recommendation.before}</code>
                        </div>
                      </div>
                      
                      <div>
                        <h5 className="text-sm font-medium text-gray-900 mb-2">Depois:</h5>
                        <div className="bg-green-50 border border-green-200 rounded-md p-3">
                          <code className="text-sm text-green-800">{recommendation.after}</code>
                        </div>
                      </div>
                    </div>
                  )}

                  {recommendation.codeExample && (
                    <div className="mb-4">
                      <div className="flex items-center justify-between mb-2">
                        <h5 className="text-sm font-medium text-gray-900">Exemplo de Código:</h5>
                        
                        <button
                          onClick={() => copyCode(recommendation.codeExample!, recommendation.id)}
                          className="flex items-center space-x-1 px-2 py-1 text-xs text-gray-600 hover:text-gray-800 border border-gray-300 rounded hover:bg-gray-50 transition-colors"
                        >
                          {copiedCode === recommendation.id ? (
                            <>
                              <Check className="h-3 w-3" />
                              <span>Copiado!</span>
                            </>
                          ) : (
                            <>
                              <Copy className="h-3 w-3" />
                              <span>Copiar</span>
                            </>
                          )}
                        </button>
                      </div>
                      
                      <div className="bg-gray-900 text-gray-100 rounded-md p-4 overflow-x-auto">
                        <pre className="text-sm">
                          <code>{recommendation.codeExample}</code>
                        </pre>
                      </div>
                    </div>
                  )}

                  {recommendation.documentation && (
                    <div className="flex items-center space-x-2 text-sm text-blue-600">
                      <ExternalLink className="h-4 w-4" />
                      <a
                        href={recommendation.documentation}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:underline"
                      >
                        Ver documentação oficial
                      </a>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {filteredRecommendations.length === 0 && (
        <div className="p-8 text-center text-gray-500">
          <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>Nenhuma recomendação encontrada com os filtros selecionados.</p>
        </div>
      )}
    </div>
  );
};

function generateHTMLReport(report: ReportData): string {
  return `
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Responsividade - ${report.url}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { padding: 30px; border-bottom: 1px solid #e0e0e0; }
        .scores { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; padding: 20px; }
        .score-card { text-align: center; padding: 20px; border-radius: 8px; }
        .score-value { font-size: 2rem; font-weight: bold; margin-bottom: 5px; }
        .recommendations { padding: 30px; }
        .recommendation { margin-bottom: 30px; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; }
        .code-example { background: #f8f9fa; padding: 15px; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 14px; overflow-x: auto; }
        .summary { padding: 20px; background: #f8f9fa; border-radius: 8px; margin: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Relatório de Responsividade</h1>
            <p><strong>URL:</strong> ${report.url}</p>
            <p><strong>Data:</strong> ${new Date(report.timestamp).toLocaleString('pt-BR')}</p>
        </div>
        
        <div class="scores">
            <div class="score-card" style="background: ${report.score.mobile >= 80 ? '#d4edda' : report.score.mobile >= 60 ? '#fff3cd' : '#f8d7da'}">
                <div class="score-value" style="color: ${report.score.mobile >= 80 ? '#155724' : report.score.mobile >= 60 ? '#856404' : '#721c24'}">${report.score.mobile}</div>
                <div>Mobile</div>
            </div>
            <div class="score-card" style="background: ${report.score.tablet >= 80 ? '#d4edda' : report.score.tablet >= 60 ? '#fff3cd' : '#f8d7da'}">
                <div class="score-value" style="color: ${report.score.tablet >= 80 ? '#155724' : report.score.tablet >= 60 ? '#856404' : '#721c24'}">${report.score.tablet}</div>
                <div>Tablet</div>
            </div>
            <div class="score-card" style="background: ${report.score.desktop >= 80 ? '#d4edda' : report.score.desktop >= 60 ? '#fff3cd' : '#f8d7da'}">
                <div class="score-value" style="color: ${report.score.desktop >= 80 ? '#155724' : report.score.desktop >= 60 ? '#856404' : '#721c24'}">${report.score.desktop}</div>
                <div>Desktop</div>
            </div>
            <div class="score-card" style="background: #e9ecef;">
                <div class="score-value">${report.score.overall}</div>
                <div>Geral</div>
            </div>
        </div>
        
        <div class="summary">
            <h3>Sumário Executivo</h3>
            <p>${report.summary}</p>
        </div>
        
        <div class="recommendations">
            <h2>Recomendações</h2>
            ${report.recommendations.map(rec => `
                <div class="recommendation">
                    <h4>${rec.title}</h4>
                    <p><strong>Categoria:</strong> ${rec.category}</p>
                    <p><strong>Prioridade:</strong> ${rec.priority}</p>
                    <p>${rec.description}</p>
                    ${rec.codeExample ? `
                        <div class="code-example">
                            <strong>Exemplo de código:</strong><br>
                            ${rec.codeExample.replace(/</g, '&lt;').replace(/>/g, '&gt;')}
                        </div>
                    ` : ''}
                </div>
            `).join('')}
        </div>
    </div>
</body>
</html>
  `;
}

export default Report;