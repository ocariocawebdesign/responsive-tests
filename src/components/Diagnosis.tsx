import React, { useState } from 'react';
import { AlertTriangle, AlertCircle, Info, ChevronDown, ChevronUp, Smartphone, Tablet, Monitor } from 'lucide-react';

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

interface DiagnosisProps {
  issues: Issue[];
}

const Diagnosis: React.FC<DiagnosisProps> = ({ issues }) => {
  const [expandedIssues, setExpandedIssues] = useState<Set<string>>(new Set());
  const [filterDevice, setFilterDevice] = useState<string>('all');
  const [filterType, setFilterType] = useState<string>('all');

  const toggleIssue = (issueId: string) => {
    const newExpanded = new Set(expandedIssues);
    if (newExpanded.has(issueId)) {
      newExpanded.delete(issueId);
    } else {
      newExpanded.add(issueId);
    }
    setExpandedIssues(newExpanded);
  };

  const getSeverityIcon = (type: string) => {
    switch (type) {
      case 'critical':
        return <AlertTriangle className="h-5 w-5 text-red-500" />;
      case 'warning':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      case 'info':
        return <Info className="h-5 w-5 text-blue-500" />;
      default:
        return <Info className="h-5 w-5 text-gray-500" />;
    }
  };

  const getSeverityColor = (type: string) => {
    switch (type) {
      case 'critical':
        return 'border-red-200 bg-red-50';
      case 'warning':
        return 'border-yellow-200 bg-yellow-50';
      case 'info':
        return 'border-blue-200 bg-blue-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  const getDeviceIcon = (device: string) => {
    const icons = {
      mobile: Smartphone,
      tablet: Tablet,
      desktop: Monitor,
      '4k': Monitor
    };
    return icons[device as keyof typeof icons] || Monitor;
  };

  const getDeviceColor = (device: string) => {
    const colors = {
      mobile: 'bg-green-100 text-green-800',
      tablet: 'bg-blue-100 text-blue-800',
      desktop: 'bg-purple-100 text-purple-800',
      '4k': 'bg-indigo-100 text-indigo-800'
    };
    return colors[device as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const filteredIssues = issues.filter(issue => {
    const deviceMatch = filterDevice === 'all' || issue.device === filterDevice;
    const typeMatch = filterType === 'all' || issue.type === filterType;
    return deviceMatch && typeMatch;
  });

  const stats = {
    critical: issues.filter(i => i.type === 'critical').length,
    warning: issues.filter(i => i.type === 'warning').length,
    info: issues.filter(i => i.type === 'info').length,
    total: issues.length
  };

  if (issues.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
        <div className="text-gray-500">
          <Info className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Nenhum problema detectado</h3>
          <p className="text-gray-600">Seu site parece estar funcionando bem em todos os dispositivos!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Diagnóstico de Responsividade</h3>
            <p className="text-sm text-gray-600">
              {stats.total} problemas encontrados • {stats.critical} críticos • {stats.warning} avisos • {stats.info} informativos
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-4">
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">Dispositivo:</label>
            <select
              value={filterDevice}
              onChange={(e) => setFilterDevice(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Todos</option>
              <option value="mobile">Mobile</option>
              <option value="tablet">Tablet</option>
              <option value="desktop">Desktop</option>
              <option value="4k">4K</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">Tipo:</label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Todos</option>
              <option value="critical">Crítico</option>
              <option value="warning">Aviso</option>
              <option value="info">Informativo</option>
            </select>
          </div>
        </div>
      </div>

      <div className="divide-y divide-gray-200">
        {filteredIssues.map((issue) => {
          const isExpanded = expandedIssues.has(issue.id);
          const DeviceIcon = getDeviceIcon(issue.device);
          const deviceColor = getDeviceColor(issue.device);

          return (
            <div key={issue.id} className={`p-4 border-l-4 ${getSeverityColor(issue.type)}`}>
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 mt-1">
                  {getSeverityIcon(issue.type)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-medium text-gray-900">
                      {issue.title}
                    </h4>
                    
                    <div className="flex items-center space-x-2">
                      <div className={`px-2 py-1 rounded-full text-xs font-medium ${deviceColor}`}>
                        <div className="flex items-center space-x-1">
                          <DeviceIcon className="h-3 w-3" />
                          <span className="capitalize">{issue.device}</span>
                        </div>
                      </div>
                      
                      <button
                        onClick={() => toggleIssue(issue.id)}
                        className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                      >
                        {isExpanded ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  </div>

                  <p className="text-sm text-gray-600 mt-1">
                    {issue.description}
                  </p>

                  {issue.element && (
                    <p className="text-xs text-gray-500 mt-1">
                      Elemento: <code className="bg-gray-100 px-1 py-0.5 rounded">{issue.element}</code>
                    </p>
                  )}

                  {isExpanded && issue.suggestion && (
                    <div className="mt-3 p-3 bg-white border border-gray-200 rounded-md">
                      <h5 className="text-sm font-medium text-gray-900 mb-2">Sugestão:</h5>
                      <p className="text-sm text-gray-700">{issue.suggestion}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {filteredIssues.length === 0 && (
        <div className="p-8 text-center text-gray-500">
          <Info className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>Nenhum problema encontrado com os filtros selecionados.</p>
        </div>
      )}
    </div>
  );
};

export default Diagnosis;
