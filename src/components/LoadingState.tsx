import React from 'react';
import { Loader2, Camera, Smartphone, Tablet, Monitor } from 'lucide-react';

interface LoadingStateProps {
  status: string;
  currentStep?: number;
  totalSteps?: number;
}

const LoadingState: React.FC<LoadingStateProps> = ({ 
  status, 
  currentStep = 1, 
  totalSteps = 4 
}) => {
  const steps = [
    { icon: Camera, label: 'Capturando screenshots' },
    { icon: Smartphone, label: 'Analisando mobile' },
    { icon: Tablet, label: 'Analisando tablet' },
    { icon: Monitor, label: 'Analisando desktop' }
  ];

  return (
    <div className="flex flex-col items-center justify-center p-8 bg-white rounded-lg shadow-sm border">
      <div className="relative mb-6">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
        <div className="absolute inset-0 flex items-center justify-center">
          <Loader2 className="h-8 w-8 text-blue-600 animate-spin" />
        </div>
      </div>

      <h3 className="text-lg font-semibold text-gray-900 mb-2">Analisando Responsividade</h3>
      <p className="text-gray-600 mb-6 text-center max-w-md">{status}</p>

      <div className="w-full max-w-md">
        <div className="flex justify-between mb-2">
          {steps.map((step, index) => {
            const Icon = step.icon;
            const isActive = index + 1 === currentStep;
            const isCompleted = index + 1 < currentStep;
            
            return (
              <div key={index} className="flex flex-col items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 ${
                  isCompleted ? 'bg-green-500 text-white' : 
                  isActive ? 'bg-blue-600 text-white' : 
                  'bg-gray-200 text-gray-400'
                }`}>
                  <Icon className="h-5 w-5" />
                </div>
                <span className={`text-xs mt-1 text-center ${
                  isActive ? 'text-blue-600 font-medium' : 
                  isCompleted ? 'text-green-600' : 
                  'text-gray-400'
                }`}>
                  {step.label}
                </span>
              </div>
            );
          })}
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${((currentStep - 1) / totalSteps) * 100}%` }}
          ></div>
        </div>
        
        <div className="text-center mt-2">
          <span className="text-sm text-gray-500">
            Passo {currentStep} de {totalSteps}
          </span>
        </div>
      </div>
    </div>
  );
};

export default LoadingState;