import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import mermaid from 'mermaid';

mermaid.initialize({ startOnLoad: false, theme: 'dark' });

// ... existing EvalDashboard ...
function EvalDashboard() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    fetch(`${apiUrl}/eval/results`)
      .then(res => {
        if (!res.ok) throw new Error("Failed to fetch evaluation results");
        return res.json();
      })
      .then(data => {
        if (data.error) throw new Error(data.error);
        setResults(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="text-center py-20 text-xl text-content-muted">Loading evaluation data...</div>;
  if (error) return <div className="bg-accent-hover/20 border border-red-500 p-6 rounded-xl text-accent">{error}</div>;

  const avgLatency = results.reduce((acc, r) => acc + r.latency_sec, 0) / results.length;
  const precision = (results.filter(r => r.is_hit).length / results.length) * 100;

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
        <div className="bg-bg-bg-tertiary/50 backdrop-blur-md border border-border-secondary p-8 rounded-2xl shadow-xl transition hover:border-blue-500/50">
          <h3 className="text-lg font-medium text-content-muted mb-2">Average Latency</h3>
          <div className="text-5xl font-bold text-accent">{avgLatency.toFixed(2)}s</div>
        </div>
        <div className="bg-bg-bg-tertiary/50 backdrop-blur-md border border-border-secondary p-8 rounded-2xl shadow-xl transition hover:border-emerald-500/50">
          <h3 className="text-lg font-medium text-content-muted mb-2">Retrieval Precision</h3>
          <div className="text-5xl font-bold text-accent">{precision.toFixed(1)}%</div>
        </div>
      </div>

      <div className="bg-bg-bg-tertiary/50 backdrop-blur-md border border-border-secondary rounded-2xl overflow-hidden shadow-xl">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-bg-tertiary border-b border-border-secondary">
              <th className="p-4 font-semibold text-content-secondary">Question</th>
              <th className="p-4 font-semibold text-content-secondary">Expected File</th>
              <th className="p-4 font-semibold text-content-secondary">Result</th>
              <th className="p-4 font-semibold text-content-secondary">Latency</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r, i) => (
              <tr key={i} className="border-b border-border-secondary/50 hover:bg-bg-bg-quaternary/30 transition">
                <td className="p-4 font-medium text-content-primary">{r.question}</td>
                <td className="p-4 text-content-muted text-sm font-mono">{r.expected_file}</td>
                <td className="p-4">
                  {r.is_hit ? (
                    <span className="px-3 py-1 bg-accent-hover/20 text-accent border border-accent/30 rounded-full text-xs font-bold uppercase tracking-wider">Hit</span>
                  ) : (
                    <span className="px-3 py-1 bg-accent-hover/20 text-accent border border-accent/30 rounded-full text-xs font-bold uppercase tracking-wider">Miss</span>
                  )}
                </td>
                <td className="p-4 text-content-muted text-sm font-mono">{r.latency_sec}s</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ... existing OnboardingGuide ...
function OnboardingGuide() {
  const [repoUrl, setRepoUrl] = useState("https://github.com/psf/requests-html");
  const [guide, setGuide] = useState("");
  const [status, setStatus] = useState("idle");

  const fetchGuide = async () => {
    setStatus("fetching");
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/onboarding-guide?repo_url_or_path=${encodeURIComponent(repoUrl)}`);
      const data = await res.json();
      
      if (data.status === "ready") {
        setGuide(data.markdown);
        setStatus("ready");
      } else if (data.status === "processing") {
        setStatus("processing");
      } else {
        setStatus("not_found");
      }
    } catch (err) {
      console.error(err);
      setStatus("error");
    }
  };

  return (
    <div className="bg-bg-bg-tertiary/50 backdrop-blur-md border border-border-secondary p-8 rounded-2xl shadow-xl">
      <div className="flex gap-4 mb-8">
        <input 
          type="text" 
          value={repoUrl}
          onChange={e => setRepoUrl(e.target.value)}
          className="flex-1 bg-bg-secondary border border-border-tertiary rounded-lg px-4 py-3 text-content-inverted focus:outline-none focus:border-accent transition"
          placeholder="Enter Repo URL..."
        />
        <button 
          onClick={fetchGuide}
          className="bg-accent hover:bg-accent-hover text-content-inverted px-8 py-3 rounded-lg font-semibold transition shadow-lg shadow-accent/30"
        >
          Fetch Guide
        </button>
      </div>

      <div className="prose prose-invert max-w-none">
        {status === "idle" && <p className="text-content-muted text-center py-10">Enter a repo URL to fetch its onboarding guide.</p>}
        {status === "fetching" && <p className="text-accent text-center py-10 animate-pulse">Checking guide status...</p>}
        {status === "processing" && (
          <div className="text-center py-10">
            <p className="text-accent text-xl font-bold animate-pulse mb-2">Guide is currently generating...</p>
            <p className="text-content-muted">The RAG pipeline is analyzing the repo in the background. Please try fetching again in a minute.</p>
          </div>
        )}
        {status === "not_found" && (
          <div className="text-center py-10">
            <p className="text-accent text-xl font-bold mb-2">No guide found.</p>
            <p className="text-content-muted">Make sure you have ingested this repo first via the backend.</p>
          </div>
        )}
        {status === "error" && <p className="text-red-500 text-center py-10">Network error occurred.</p>}
        {status === "ready" && (
          <div className="bg-bg-bg-secondary/50 p-8 rounded-xl border border-border-secondary mt-8">
            <ReactMarkdown>{guide}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}

// New Architecture Diagram Component
function ArchitectureDiagram() {
  const [repoUrl, setRepoUrl] = useState("https://github.com/psf/requests-html");
  const [status, setStatus] = useState("idle");
  const [svgContent, setSvgContent] = useState("");
  const graphRef = useRef(null);

  const fetchGraph = async () => {
    setStatus("fetching");
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/architecture-diagram?repo_url_or_path=${encodeURIComponent(repoUrl)}`);
      const data = await res.json();
      
      if (data.status === "ready") {
        renderMermaid(data.graph);
        setStatus("ready");
      } else {
        setStatus("not_found");
      }
    } catch (err) {
      console.error(err);
      setStatus("error");
    }
  };

  const renderMermaid = async (graphData) => {
    // Basic graph TD syntax
    let mermaidCode = "graph TD;\n";
    
    // Sort nodes to prioritize top 30 based on connectivity to avoid huge render lags
    const edgeCounts = {};
    graphData.nodes.forEach(n => edgeCounts[n] = 0);
    graphData.edges.forEach(e => {
      edgeCounts[e.source] = (edgeCounts[e.source] || 0) + 1;
      edgeCounts[e.target] = (edgeCounts[e.target] || 0) + 1;
    });
    
    // Select top N nodes
    const topNodes = Object.keys(edgeCounts).sort((a,b) => edgeCounts[b] - edgeCounts[a]).slice(0, 30);
    const nodeSet = new Set(topNodes);

    graphData.edges.forEach(edge => {
      if (nodeSet.has(edge.source) && nodeSet.has(edge.target)) {
        // Sanitize node names for Mermaid
        const s = edge.source.replace(/[^a-zA-Z0-9]/g, '_');
        const t = edge.target.replace(/[^a-zA-Z0-9]/g, '_');
        const label = edge.type === 'call' ? 'calls' : 'imports';
        mermaidCode += `  ${s}["${edge.source}"] -->|${label}| ${t}["${edge.target}"]\n`;
      }
    });

    if (mermaidCode === "graph TD;\n") {
       mermaidCode += "  A[No connections found in top 30 nodes] --> B[Try another repo]\n";
    }

    try {
      const { svg } = await mermaid.render('mermaid-graph', mermaidCode);
      setSvgContent(svg);
    } catch (e) {
      console.error("Mermaid rendering failed", e);
      setSvgContent(`<div class="text-accent">Failed to render graph. The repository structure might be too complex or invalid.</div>`);
    }
  };

  return (
    <div className="bg-bg-bg-tertiary/50 backdrop-blur-md border border-border-secondary p-8 rounded-2xl shadow-xl">
      <div className="flex gap-4 mb-8">
        <input 
          type="text" 
          value={repoUrl}
          onChange={e => setRepoUrl(e.target.value)}
          className="flex-1 bg-bg-secondary border border-border-tertiary rounded-lg px-4 py-3 text-content-inverted focus:outline-none focus:border-accent transition"
          placeholder="Enter Repo URL..."
        />
        <button 
          onClick={fetchGraph}
          className="bg-accent hover:bg-accent-hover text-content-inverted px-8 py-3 rounded-lg font-semibold transition shadow-lg shadow-accent/30"
        >
          Generate Diagram
        </button>
      </div>

      <div className="bg-bg-bg-secondary/80 rounded-xl border border-border-secondary p-8 min-h-[400px] flex items-center justify-center overflow-auto">
        {status === "idle" && <p className="text-content-muted text-center">Enter a repo URL to generate an architecture diagram.</p>}
        {status === "fetching" && <p className="text-accent text-center animate-pulse">Analyzing repository structure...</p>}
        {status === "not_found" && <p className="text-accent text-center font-bold">No data found. Make sure you have ingested this repo first.</p>}
        {status === "error" && <p className="text-red-500 text-center">Network error occurred.</p>}
        {status === "ready" && (
          <div 
            className="w-full flex justify-center text-content-primary"
            dangerouslySetInnerHTML={{ __html: svgContent }} 
          />
        )}
      </div>
    </div>
  );
}

// New Diff Explainer Component
function DiffExplainer() {
  const [repoUrl, setRepoUrl] = useState("https://github.com/psf/requests-html");
  const [diffText, setDiffText] = useState("");
  const [explanation, setExplanation] = useState("");
  const [status, setStatus] = useState("idle");

  const explainDiff = async () => {
    if (!diffText.trim()) return;
    setStatus("fetching");
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/explain-diff`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_url_or_path: repoUrl,
          diff_text: diffText
        })
      });
      const data = await res.json();
      
      if (res.ok) {
        setExplanation(data.explanation);
        setStatus("ready");
      } else {
        throw new Error(data.detail || "Error fetching explanation");
      }
    } catch (err) {
      console.error(err);
      setStatus("error");
    }
  };

  return (
    <div className="bg-bg-bg-tertiary/50 backdrop-blur-md border border-border-secondary p-8 rounded-2xl shadow-xl flex flex-col gap-6">
      <div className="flex gap-4">
        <input 
          type="text" 
          value={repoUrl}
          onChange={e => setRepoUrl(e.target.value)}
          className="flex-1 bg-bg-secondary border border-border-tertiary rounded-lg px-4 py-3 text-content-inverted focus:outline-none focus:border-accent transition"
          placeholder="Enter Repo URL..."
        />
        <button 
          onClick={explainDiff}
          disabled={status === "fetching"}
          className="bg-accent hover:bg-accent-hover disabled:opacity-50 text-content-inverted px-8 py-3 rounded-lg font-semibold transition shadow-lg shadow-accent/30"
        >
          {status === "fetching" ? "Analyzing..." : "Explain Diff"}
        </button>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-full min-h-[500px]">
        <div className="flex flex-col gap-2">
          <label className="text-content-muted font-medium">Paste Git Diff</label>
          <textarea
            value={diffText}
            onChange={e => setDiffText(e.target.value)}
            className="flex-1 bg-bg-bg-secondary/80 font-mono text-sm border border-border-tertiary rounded-lg p-4 text-content-secondary focus:outline-none focus:border-accent transition resize-none"
            placeholder="diff --git a/file b/file..."
          />
        </div>
        
        <div className="flex flex-col gap-2">
          <label className="text-content-muted font-medium">Explanation & Impact</label>
          <div className="flex-1 bg-bg-bg-secondary/50 border border-border-secondary rounded-lg p-6 overflow-auto">
            {status === "idle" && <p className="text-content-muted text-center mt-10">Paste a diff and click Explain to see the analysis.</p>}
            {status === "fetching" && <p className="text-accent text-center mt-10 animate-pulse">Running hybrid retrieval and analyzing downstream impact...</p>}
            {status === "error" && <p className="text-red-500 text-center mt-10">Failed to generate explanation. Check your backend connection.</p>}
            {status === "ready" && (
              <div className="prose prose-invert max-w-none text-content-secondary">
                <ReactMarkdown>{explanation}</ReactMarkdown>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// New Repo Comparison Component
function RepoComparison() {
  const [repoUrl1, setRepoUrl1] = useState("https://github.com/psf/requests-html");
  const [repoUrl2, setRepoUrl2] = useState("https://github.com/psf/requests");
  const [query, setQuery] = useState("");
  const [comparison, setComparison] = useState("");
  const [status, setStatus] = useState("idle");

  const compareRepos = async () => {
    if (!query.trim() || !repoUrl1.trim() || !repoUrl2.trim()) return;
    setStatus("fetching");
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/compare-repos`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_url_1: repoUrl1,
          repo_url_2: repoUrl2,
          query: query
        })
      });
      const data = await res.json();
      
      if (res.ok) {
        setComparison(data.comparison);
        setStatus("ready");
      } else {
        throw new Error(data.detail || "Error comparing repos");
      }
    } catch (err) {
      console.error(err);
      setStatus("error");
    }
  };

  return (
    <div className="bg-bg-bg-tertiary/50 backdrop-blur-md border border-border-secondary p-8 rounded-2xl shadow-xl flex flex-col gap-6">
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1 flex flex-col gap-2">
          <label className="text-content-muted font-medium text-sm">Repository 1 URL</label>
          <input 
            type="text" 
            value={repoUrl1}
            onChange={e => setRepoUrl1(e.target.value)}
            className="w-full bg-bg-secondary border border-border-tertiary rounded-lg px-4 py-3 text-content-inverted focus:outline-none focus:border-accent transition"
          />
        </div>
        <div className="flex-1 flex flex-col gap-2">
          <label className="text-content-muted font-medium text-sm">Repository 2 URL</label>
          <input 
            type="text" 
            value={repoUrl2}
            onChange={e => setRepoUrl2(e.target.value)}
            className="w-full bg-bg-secondary border border-border-tertiary rounded-lg px-4 py-3 text-content-inverted focus:outline-none focus:border-accent transition"
          />
        </div>
      </div>
      
      <div className="flex gap-4 items-end">
        <div className="flex-1 flex flex-col gap-2">
          <label className="text-content-muted font-medium text-sm">Comparison Query</label>
          <input 
            type="text" 
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && compareRepos()}
            className="w-full bg-bg-secondary border border-border-tertiary rounded-lg px-4 py-3 text-content-inverted focus:outline-none focus:border-accent transition"
            placeholder="e.g. How does session handling differ between these two?"
          />
        </div>
        <button 
          onClick={compareRepos}
          disabled={status === "fetching" || !query.trim()}
          className="bg-accent hover:bg-accent-hover disabled:opacity-50 text-content-inverted px-8 py-3 rounded-lg font-semibold transition shadow-lg shadow-accent/30"
        >
          {status === "fetching" ? "Comparing..." : "Compare Repos"}
        </button>
      </div>

      <div className="bg-bg-bg-secondary/50 border border-border-secondary rounded-lg p-6 min-h-[300px] overflow-auto mt-4">
        {status === "idle" && <p className="text-content-muted text-center mt-10">Enter two repos and ask a question to see a comparative analysis.</p>}
        {status === "fetching" && <p className="text-accent text-center mt-10 animate-pulse">Running dual retrieval and synthesizing comparison...</p>}
        {status === "error" && <p className="text-red-500 text-center mt-10">Failed to generate comparison. Ensure both repos are ingested.</p>}
        {status === "ready" && (
          <div className="prose prose-invert max-w-none text-content-secondary">
            <ReactMarkdown>{comparison}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}

// New Code Risks Component
function CodeRisks() {
  const [repoUrl, setRepoUrl] = useState("https://github.com/psf/requests-html");
  const [smells, setSmells] = useState([]);
  const [status, setStatus] = useState("idle");
  const [explanation, setExplanation] = useState("");
  const [explaining, setExplaining] = useState(false);
  const [activeSmell, setActiveSmell] = useState(null);

  const fetchSmells = async () => {
    setStatus("fetching");
    setExplanation("");
    setActiveSmell(null);
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/code-smells?repo_url_or_path=${encodeURIComponent(repoUrl)}`);
      const data = await res.json();
      
      if (data.status === "ready") {
        setSmells(data.smells);
        setStatus("ready");
      } else {
        setStatus("not_found");
        setSmells([]);
      }
    } catch (err) {
      console.error(err);
      setStatus("error");
    }
  };

  const explainSmell = async (smell) => {
    setExplaining(true);
    setActiveSmell(smell);
    setExplanation("");
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/explain-smell`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_url_or_path: repoUrl,
          file_path: smell.file_path,
          smell_name: smell.name
        })
      });
      const data = await res.json();
      if (res.ok) {
        setExplanation(data.explanation);
      } else {
        setExplanation("Error generating explanation.");
      }
    } catch (err) {
      console.error(err);
      setExplanation("Network error.");
    } finally {
      setExplaining(false);
    }
  };

  return (
    <div className="bg-bg-bg-tertiary/50 backdrop-blur-md border border-border-secondary p-8 rounded-2xl shadow-xl">
      <div className="flex gap-4 mb-8">
        <input 
          type="text" 
          value={repoUrl}
          onChange={e => setRepoUrl(e.target.value)}
          className="flex-1 bg-bg-secondary border border-border-tertiary rounded-lg px-4 py-3 text-content-inverted focus:outline-none focus:border-accent transition"
          placeholder="Enter Repo URL..."
        />
        <button 
          onClick={fetchSmells}
          className="bg-accent hover:bg-accent-hover text-content-inverted px-8 py-3 rounded-lg font-semibold transition shadow-lg shadow-accent/30"
        >
          Scan Risks
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-bg-bg-secondary/50 border border-border-secondary rounded-xl overflow-hidden min-h-[400px]">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-bg-tertiary border-b border-border-secondary text-content-secondary">
                <th className="p-4 font-semibold">File</th>
                <th className="p-4 font-semibold">Symbol</th>
                <th className="p-4 font-semibold">Complexity</th>
                <th className="p-4 font-semibold">Action</th>
              </tr>
            </thead>
            <tbody>
              {status === "idle" && <tr><td colSpan="4" className="text-center p-8 text-content-muted">Click Scan Risks to load code smells.</td></tr>}
              {status === "fetching" && <tr><td colSpan="4" className="text-center p-8 text-accent animate-pulse">Loading smells...</td></tr>}
              {status === "not_found" && <tr><td colSpan="4" className="text-center p-8 text-red-500">No risks found or repo not ingested.</td></tr>}
              {status === "ready" && smells.length === 0 && <tr><td colSpan="4" className="text-center p-8 text-accent">No high-complexity functions found! Code is clean.</td></tr>}
              
              {status === "ready" && smells.map((smell, idx) => (
                <tr key={idx} className={`border-b border-border-secondary/50 transition ${activeSmell === smell ? 'bg-red-900/20' : 'hover:bg-bg-bg-quaternary/30'}`}>
                  <td className="p-4 text-sm font-mono text-content-muted">{smell.file_path}</td>
                  <td className="p-4 text-content-primary font-medium">{smell.name}</td>
                  <td className="p-4">
                    <span className="px-3 py-1 bg-accent-hover/20 text-accent border border-accent/30 rounded-full text-xs font-bold">
                      {smell.complexity}
                    </span>
                  </td>
                  <td className="p-4">
                    <button 
                      onClick={() => explainSmell(smell)}
                      disabled={explaining}
                      className="text-xs bg-bg-quaternary hover:bg-gray-600 text-content-inverted px-3 py-1.5 rounded disabled:opacity-50 transition"
                    >
                      Explain
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="bg-bg-bg-secondary/80 border border-border-secondary rounded-xl p-6 min-h-[400px] overflow-auto">
          <h3 className="text-lg font-semibold text-content-secondary mb-4 border-b border-border-secondary pb-2">AI Risk Analysis</h3>
          {!activeSmell && !explaining && <p className="text-content-muted mt-10 text-center">Click 'Explain' on a code smell to generate an analysis.</p>}
          {explaining && <p className="text-accent text-center mt-10 animate-pulse">Retrieving code block and analyzing logic...</p>}
          {explanation && (
            <div className="prose prose-invert max-w-none text-content-secondary">
              <ReactMarkdown>{explanation}</ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// New Code Q&A Component with Export
function CodeQA() {
  const [repoUrl, setRepoUrl] = useState("https://github.com/psf/requests-html");
  const [query, setQuery] = useState("");
  const [history, setHistory] = useState([]);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState(null);

  const handleAsk = async () => {
    if (!query.trim() || !repoUrl.trim()) return;
    const userQ = query;
    setQuery("");
    setError(null);
    setHistory(prev => [...prev, { role: "user", content: userQ }]);
    setAsking(true);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_url_or_path: repoUrl,
          query: userQ,
          limit: 5
        })
      });
      const data = await res.json();
      
      if (res.ok) {
        setHistory(prev => [...prev, { 
          role: "assistant", 
          content: data.answer,
          citations: data.citations
        }]);
      } else {
        throw new Error(data.detail || "Error asking question");
      }
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setAsking(false);
    }
  };

  const exportSession = () => {
    if (history.length === 0) return;
    
    let md = `# Codebase Q&A Session for ${repoUrl}\n\n`;
    history.forEach(msg => {
      if (msg.role === "user") {
        md += `## Question\n\n**${msg.content}**\n\n`;
      } else {
        md += `## Answer\n\n${msg.content}\n\n---\n\n`;
      }
    });

    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `qa_session_${new Date().getTime()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-bg-bg-tertiary/50 backdrop-blur-md border border-border-secondary p-8 rounded-2xl shadow-xl flex flex-col gap-6">
      <div className="flex gap-4">
        <input 
          type="text" 
          value={repoUrl}
          onChange={e => setRepoUrl(e.target.value)}
          className="flex-1 bg-bg-secondary border border-border-tertiary rounded-lg px-4 py-3 text-content-inverted focus:outline-none focus:border-accent transition"
          placeholder="Enter Repo URL..."
        />
        <button 
          type="button"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            exportSession();
          }}
          disabled={history.length === 0}
          className="bg-bg-quaternary hover:bg-gray-600 disabled:opacity-50 text-content-inverted px-6 py-3 rounded-lg font-semibold transition"
        >
          Export Session
        </button>
      </div>

      <div className="bg-bg-bg-secondary/80 border border-border-secondary rounded-xl p-6 h-[500px] overflow-auto flex flex-col gap-6">
        {history.length === 0 && <p className="text-content-muted text-center mt-20">Ask a question about the codebase to start the session.</p>}
        
        {history.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] p-4 rounded-xl ${msg.role === "user" ? "bg-accent/20 border border-accent/30 text-cyan-50" : "bg-bg-tertiary border border-border-tertiary text-content-primary"}`}>
              {msg.role === "user" ? (
                <p className="font-medium">{msg.content}</p>
              ) : (
                <div className="prose prose-invert max-w-none text-sm">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              )}
            </div>
          </div>
        ))}
        {asking && (
          <div className="flex justify-start">
            <div className="max-w-[80%] p-4 rounded-xl bg-bg-tertiary border border-border-tertiary text-content-muted animate-pulse">
              Generating answer...
            </div>
          </div>
        )}
        {error && <p className="text-red-500 text-center">{error}</p>}
      </div>

      <div className="flex gap-4">
        <input 
          type="text" 
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleAsk()}
          className="flex-1 bg-bg-secondary border border-border-tertiary rounded-lg px-4 py-3 text-content-inverted focus:outline-none focus:border-accent transition"
          placeholder="Ask a question about the code..."
        />
        <button 
          onClick={handleAsk}
          disabled={asking || !query.trim()}
          className="bg-accent hover:bg-accent-hover disabled:opacity-50 text-content-inverted px-8 py-3 rounded-lg font-semibold transition shadow-lg shadow-accent/30"
        >
          Ask
        </button>
      </div>
    </div>
  );
}


function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [theme, setTheme] = useState("dark");

  const toggleTheme = () => setTheme(theme === "dark" ? "light" : "dark");


  const navItems = [
    { id: "dashboard", label: "Eval Dashboard" },
    { id: "guide", label: "Onboarding Guide" },
    { id: "architecture", label: "Architecture Diagram" },
    { id: "diff", label: "Diff Explainer" },
    { id: "compare", label: "Repo Comparison" },
    { id: "risks", label: "Code Risks" },
    { id: "qa", label: "Q&A Session" },
  ];

  return (
    <div className={`${theme} min-h-screen bg-bg-primary text-content-primary font-sans flex`}>
      {/* Sidebar Navigation */}
      <aside className="w-72 bg-bg-secondary border-r border-border-primary flex flex-col h-screen sticky top-0 shadow-2xl z-10">
        <div className="p-8 pb-4">
          <h1 className="text-3xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
            Codebase Explorer
          </h1>
          <p className="text-content-muted text-sm mt-1 font-medium tracking-wide">Codebase Intelligence</p>
        </div>
        
        <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
          {navItems.map(item => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full text-left px-5 py-3.5 rounded-xl font-medium transition-all duration-200 ${
                activeTab === item.id 
                  ? 'bg-accent text-content-inverted shadow-lg shadow-accent/25 transform scale-[1.02]' 
                  : 'text-content-muted hover:bg-bg-bg-tertiary/80 hover:text-content-primary'
              }`}
            >
              {item.label}
            </button>
          ))}
        </nav>
        

        <div className="p-6 border-t border-border-primary flex justify-between items-center">
          <div className="flex items-center gap-3 text-content-muted text-xs">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
            System Online
          </div>
          <button onClick={toggleTheme} className="text-content-muted hover:text-content-primary transition p-2 rounded-lg hover:bg-bg-tertiary">
            {theme === "dark" ? "☀️" : "🌙"}
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 p-10 overflow-x-hidden">
        <div className="max-w-7xl mx-auto space-y-8">
          <header className="mb-10">
            <h2 className="text-4xl font-bold text-content-primary tracking-tight">
              {navItems.find(i => i.id === activeTab)?.label}
            </h2>
            <div className="h-1 w-20 bg-accent-hover rounded-full mt-4 opacity-50"></div>
          </header>

          <div className="animate-fade-in-up">
            {activeTab === "dashboard" && <EvalDashboard />}
            {activeTab === "guide" && <OnboardingGuide />}
            {activeTab === "architecture" && <ArchitectureDiagram />}
            {activeTab === "diff" && <DiffExplainer />}
            {activeTab === "compare" && <RepoComparison />}
            {activeTab === "risks" && <CodeRisks />}
            {activeTab === "qa" && <CodeQA />}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
