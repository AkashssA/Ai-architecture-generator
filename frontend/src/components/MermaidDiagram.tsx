import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
});

interface MermaidDiagramProps {
  chart: string;
}

export const MermaidDiagram: React.FC<MermaidDiagramProps> = ({ chart }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string>('');
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const renderDiagram = async () => {
      if (!chart || !containerRef.current) return;
      
      try {
        setError('');
        // Generate a unique ID for the SVG
        const id = `mermaid-${Math.random().toString(36).substring(2, 9)}`;
        const { svg: renderResult } = await mermaid.render(id, chart);
        setSvg(renderResult);
      } catch (err) {
        console.error('Mermaid rendering error:', err);
        setError('Failed to render diagram. The syntax might be invalid.');
      }
    };

    renderDiagram();
  }, [chart]);

  if (error) {
    return <div style={{ color: 'red', padding: '1rem' }}>{error}</div>;
  }

  return (
    <div 
      ref={containerRef}
      className="mermaid-diagram-container"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
};
