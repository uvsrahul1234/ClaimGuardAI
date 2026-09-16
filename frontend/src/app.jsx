import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';

function App() {
  const [documentText, setDocumentText] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: documentText }),
      });
      const data = await response.json();
      setResults(data.data);
    } catch (error) {
      console.error("Analysis failed", error);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-3xl mx-auto space-y-6">
        <h1 className="text-3xl font-bold text-blue-900">ClaimGuard AI Assistant</h1>
        <p className="text-gray-600">Paste your medical bill or EOB text below for a plain-language analysis.</p>
        {/* <ReactMarkdown className="text-gray-600 prose">Paste your medical bill or EOB text below for a plain-language analysis.</ReactMarkdown> */}
        
        <textarea
          className="w-full p-4 border rounded shadow-sm h-48"
          placeholder="Paste medical bill text here..."
          value={documentText}
          onChange={(e) => setDocumentText(e.target.value)}
        />
        
        <button 
          onClick={handleAnalyze}
          disabled={loading}
          className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Analyzing Workflow...' : 'Analyze Document'}
        </button>

        {results && (
          <div className="bg-white p-6 rounded shadow-md space-y-4">
            <h2 className="text-2xl font-semibold">Analysis Results</h2>
            
            <div>
              <h3 className="font-bold text-gray-700">Plain English Summary:</h3>
              <ReactMarkdown className="text-gray-600 prose">{results.summary}</ReactMarkdown>
            </div>

            <div>
              <h3 className="font-bold text-gray-700">Questions to Ask Your Provider:</h3>
              {/* We replaced the <ul> map with ReactMarkdown and joined the array */}
              <ReactMarkdown className="text-gray-600 prose">
                {Array.isArray(results.questions) 
                  ? results.questions.join('\n\n') 
                  : results.questions}
              </ReactMarkdown>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

export default App;