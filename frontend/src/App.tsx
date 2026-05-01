import { useState } from 'react';
import axios from 'axios';
import { 
  Sparkles, 
  Cpu, 
  Server, 
  Database, 
  LayoutTemplate,
  Activity,
  Code
} from 'lucide-react';
import { MermaidDiagram } from './components/MermaidDiagram';
import './index.css';

interface ComponentDef {
  name: string;
  kind: string;
  responsibilities: string[];
  communicates_with: string[];
}

interface ApiEndpoint {
  method: string;
  path: string;
  purpose: string;
}

interface ArchitectureResponse {
  title: string;
  components: ComponentDef[];
  description: string;
  mermaid_diagram: string;
  api_design: ApiEndpoint[];
  scaling_strategy: string;
}

function App() {
  const [prompt, setPrompt] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ArchitectureResponse | null>(null);
  const [error, setError] = useState('');

  const generateArchitecture = async () => {
    if (!prompt.trim()) return;
    
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      };
      
      if (apiKey) {
        headers['X-API-Key'] = apiKey;
      }

      const response = await axios.post<ArchitectureResponse>(
        '/api/generate-architecture',
        { system_prompt: prompt },
        { headers }
      );

      setResult(response.data);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || err.message || 'An error occurred during generation.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1>ArchitectAI</h1>
        <p>Instantly generate scalable system designs and diagrams from natural language.</p>
      </header>

      <div className="api-key-container">
        <input 
          type="password" 
          className="api-key-input"
          placeholder="Optional: API Key (X-API-Key)"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
        />
      </div>

      <div className="input-section">
        <textarea
          className="prompt-textarea"
          placeholder="e.g. Design a scalable URL shortener with high read throughput and analytics..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
              generateArchitecture();
            }
          }}
        />
        <button 
          className="generate-btn"
          onClick={generateArchitecture}
          disabled={loading || !prompt.trim()}
        >
          <Sparkles size={20} />
          {loading ? 'Generating...' : 'Generate Architecture'}
        </button>
      </div>

      {loading && (
        <div className="loader-container">
          <div className="spinner"></div>
          <p>Analyzing requirements and structuring system...</p>
        </div>
      )}

      {error && (
        <div style={{ color: 'var(--danger)', textAlign: 'center', marginBottom: '2rem' }}>
          {error}
        </div>
      )}

      {result && !loading && (
        <div className="results-container">
          <div className="card">
            <div className="card-header">
              <div className="card-icon"><LayoutTemplate size={24} /></div>
              <h2 className="card-title">{result.title}</h2>
            </div>
            <div className="card-content">
              <p>{result.description}</p>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <div className="card-icon"><Activity size={24} /></div>
              <h2 className="card-title">System Architecture Diagram</h2>
            </div>
            <div className="card-content">
              <MermaidDiagram chart={result.mermaid_diagram} />
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <div className="card-icon"><Server size={24} /></div>
              <h2 className="card-title">System Components</h2>
            </div>
            <div className="card-content">
              <div className="components-grid">
                {result.components.map((comp, idx) => (
                  <div key={idx} className="component-card">
                    <div className="component-header">
                      <span className="component-name">{comp.name}</span>
                      <span className="component-kind">{comp.kind}</span>
                    </div>
                    
                    <div className="component-section">
                      <h4>Responsibilities</h4>
                      <ul>
                        {comp.responsibilities.map((resp, i) => (
                          <li key={i}>{resp}</li>
                        ))}
                      </ul>
                    </div>

                    {comp.communicates_with && comp.communicates_with.length > 0 && (
                      <div className="component-section">
                        <h4>Communicates With</h4>
                        <ul>
                          {comp.communicates_with.map((cw, i) => (
                            <li key={i}>{cw}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {result.api_design && result.api_design.length > 0 && (
            <div className="card">
              <div className="card-header">
                <div className="card-icon"><Code size={24} /></div>
                <h2 className="card-title">API Design</h2>
              </div>
              <div className="card-content">
                <div className="api-list">
                  {result.api_design.map((api, idx) => (
                    <div key={idx} className="api-item">
                      <div className={`api-method ${api.method.toLowerCase()}`}>
                        {api.method}
                      </div>
                      <div className="api-path">{api.path}</div>
                      <div className="api-purpose">{api.purpose}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          <div className="card">
            <div className="card-header">
              <div className="card-icon"><Cpu size={24} /></div>
              <h2 className="card-title">Scaling Strategy</h2>
            </div>
            <div className="card-content">
              <p>{result.scaling_strategy}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
