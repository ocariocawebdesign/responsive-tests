import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, Maximize2, Download, Smartphone, Tablet, Monitor } from 'lucide-react';

interface ScreenshotData {
  id: string;
  device: string;
  resolution: string;
  url: string;
  fullPageUrl?: string;
}

interface ScreenshotsProps {
  screenshots: ScreenshotData[];
  analysisId: string;
}

const Screenshots: React.FC<ScreenshotsProps> = ({ screenshots, analysisId }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const deviceIcons = {
    mobile: Smartphone,
    tablet: Tablet,
    desktop: Monitor,
    '4k': Monitor
  };

  const deviceColors = {
    mobile: 'bg-green-100 text-green-800',
    tablet: 'bg-blue-100 text-blue-800',
    desktop: 'bg-purple-100 text-purple-800',
    '4k': 'bg-indigo-100 text-indigo-800'
  };

  if (!screenshots || screenshots.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
        <div className="text-gray-500">
          <Monitor className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>Nenhuma captura de tela disponível</p>
        </div>
      </div>
    );
  }

  const currentScreenshot = screenshots[currentIndex];
  const IconComponent = deviceIcons[currentScreenshot.device as keyof typeof deviceIcons];
  const colorClass = deviceColors[currentScreenshot.device as keyof typeof deviceColors];

  const nextScreenshot = () => {
    setCurrentIndex((prev) => (prev + 1) % screenshots.length);
  };

  const prevScreenshot = () => {
    setCurrentIndex((prev) => (prev - 1 + screenshots.length) % screenshots.length);
  };

  const downloadScreenshot = () => {
    const link = document.createElement('a');
    link.href = currentScreenshot.fullPageUrl || currentScreenshot.url;
    link.download = `screenshot-${analysisId}-${currentScreenshot.device}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg ${colorClass}`}>
              {IconComponent && <IconComponent className="h-5 w-5" />}
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Visualizações em Diferentes Dispositivos
              </h3>
              <p className="text-sm text-gray-600">
                {screenshots.length} capturas de tela disponíveis
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={downloadScreenshot}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              title="Baixar screenshot"
            >
              <Download className="h-5 w-5" />
            </button>
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              title="Tela cheia"
            >
              <Maximize2 className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      <div className="relative">
        <div className={`relative ${isFullscreen ? 'fixed inset-0 z-50 bg-black bg-opacity-90 flex items-center justify-center' : ''}`}>
          {isFullscreen && (
            <button
              onClick={() => setIsFullscreen(false)}
              className="absolute top-4 right-4 z-10 p-2 bg-white bg-opacity-90 rounded-lg text-gray-700 hover:bg-opacity-100"
            >
              ✕
            </button>
          )}

          <div className={`relative ${isFullscreen ? 'max-w-7xl max-h-screen' : 'aspect-video max-h-96'}`}>
            <img
              src={currentScreenshot.url}
              alt={`Screenshot ${currentScreenshot.device} - ${currentScreenshot.resolution}`}
              className={`w-full h-full object-contain bg-gray-50 ${isFullscreen ? 'rounded-lg' : ''}`}
            />
            
            {!isFullscreen && (
              <>
                <button
                  onClick={prevScreenshot}
                  disabled={screenshots.length <= 1}
                  className="absolute left-2 top-1/2 transform -translate-y-1/2 p-2 bg-white bg-opacity-80 rounded-full shadow-md hover:bg-opacity-100 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  <ChevronLeft className="h-5 w-5 text-gray-700" />
                </button>
                
                <button
                  onClick={nextScreenshot}
                  disabled={screenshots.length <= 1}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 bg-white bg-opacity-80 rounded-full shadow-md hover:bg-opacity-100 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  <ChevronRight className="h-5 w-5 text-gray-700" />
                </button>
              </>
            )}
          </div>
        </div>

        <div className="p-4 bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className={`px-3 py-1 rounded-full text-xs font-medium ${colorClass}`}>
                {currentScreenshot.device.toUpperCase()}
              </div>
              <span className="text-sm text-gray-600">
                {currentScreenshot.resolution}
              </span>
            </div>
            
            <div className="flex items-center space-x-2">
              {screenshots.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentIndex(index)}
                  className={`w-2 h-2 rounded-full transition-all ${
                    index === currentIndex ? 'bg-blue-600' : 'bg-gray-300 hover:bg-gray-400'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>
      </div>

      {!isFullscreen && (
        <div className="p-4 border-t border-gray-200">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {screenshots.map((screenshot, index) => {
              const IconComp = deviceIcons[screenshot.device as keyof typeof deviceIcons];
              const colorCls = deviceColors[screenshot.device as keyof typeof deviceColors];
              
              return (
                <button
                  key={screenshot.id}
                  onClick={() => setCurrentIndex(index)}
                  className={`p-3 rounded-lg border-2 transition-all ${
                    index === currentIndex
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300 bg-white'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <div className={`p-1 rounded ${colorCls}`}>
                      <IconComp className="h-4 w-4" />
                    </div>
                    <div className="text-left">
                      <div className="text-xs font-medium text-gray-900 capitalize">
                        {screenshot.device}
                      </div>
                      <div className="text-xs text-gray-500">
                        {screenshot.resolution}
                      </div>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default Screenshots;
