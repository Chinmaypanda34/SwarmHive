import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

function App() {
  const [targetUrl, setTargetUrl] = useState('');
  const [specId, setSpecId] = useState('');
  const [specs, setSpecs] = useState([]);
  const [templates, setTemplates] = useState({});
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [templateContent, setTemplateContent] = useState('');
  const [dryRunResult, setDryRunResult] = useState(null);
  const [runResult, setRunResult] = useState(null);
  const [consent, setConsent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('upload');

  // New state variables for reconnaissance and reporting
  const [reconTarget, setReconTarget] = useState('');
  const [reconScanId, setReconScanId] = useState('');
  const [reconResults, setReconResults] = useState(null);
  const [reconLoading, setReconLoading] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [reportData, setReportData] = useState(null);

  useEffect(() => {
    fetchSpecs();
    fetchTemplates();
  }, []);

  const fetchSpecs = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/specs`);
      const data = await response.json();
      setSpecs(data);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch specs. Please ensure your backend is running on port 8000.');
      setLoading(false);
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/templates`);
      const data = await response.json();
      setTemplates(data);
      setSelectedTemplate(Object.keys(data)[0] || '');
      setTemplateContent(Object.values(data)[0] || '');
    } catch (err) {
      console.error('Failed to fetch templates from backend, using local templates:', err);
      // Use your actual templates as fallback
      const localTemplates = {
        'bola_update.yaml': `name: bola-update-check
description: Try to update another user's resource.
steps:
  - id: login_owner
    method: POST
    path: /login
    body:
      username: "owner"
      password: "Password123"
    capture:
      token_owner: "$.token"
    expect_status: 200

  - id: create_resource
    method: POST
    path: /resources
    headers:
      Authorization: "Bearer {{ token_owner }}"
    body:
      name: "owner-only-resource"
      data: "secret"
    capture:
      resource_id: "$.id"
    expect_status: 200

  - id: login_attacker
    method: POST
    path: /login
    body:
      username: "attacker"
      password: "Password123"
    capture:
      token_attacker: "$.token"
    expect_status: 200

  - id: attacker_updates_owner_resource
    method: PUT
    path: /resources/{{ resource_id }}
    headers:
      Authorization: "Bearer {{ token_attacker }}"
    body:
      name: "owner-only-resource"
      data: "changed-by-attacker"
    expect_status: 200`,

        'graphql_introspect.yaml': `name: graphql-introspect
description: Run schema introspection (use only on test targets)
steps:
  - id: introspect
    method: POST
    path: /graphql
    body:
      query: "{ __schema { types { name } } }"
    expect_status: 200`,

        'idor_read.yaml': `name: idor-read-check
description: Try to read another user's profile by changing the user id.
steps:
  - id: login_userA
    method: POST
    path: /login
    body:
      username: "userA"
      password: "Password123"
    capture:
      tokenA: "$.token"
    expect_status: 200

  - id: login_userB
    method: POST
    path: /login
    body:
      username: "userB"
      password: "Password123"
    capture:
      tokenB: "$.token"
    expect_status: 200

  - id: read_as_A
    method: GET
    path: /users/1/profile
    headers:
      Authorization: "Bearer {{ tokenA }}"
    expect_status: 200

  - id: read_as_B
    method: GET
    path: /users/1/profile
    headers:
      Authorization: "Bearer {{ tokenB }}"`,

        'jwt_reuse.yaml': `name: jwt-reuse-exfil
description: Login as userA and try to access userB profile
steps:
  - id: login_userA
    method: POST
    path: /login
    body:
      username: "userA"
      password: "Password123"
    capture:
      token: "$.token"

  - id: get_userB_profile
    method: GET
    path: /users/2/profile
    headers:
      Authorization: "Bearer {{ token }}"
    expect_status: 200`
      };
      
      setTemplates(localTemplates);
      setSelectedTemplate(Object.keys(localTemplates)[0] || '');
      setTemplateContent(Object.values(localTemplates)[0] || '');
    }
  };

  const handleUpload = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/upload_spec`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: targetUrl }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Error: ${response.statusText} - ${errorData.detail}`);
      }
      const data = await response.json();
      setSpecs([...specs, data]);
      setSpecId(data.spec_id);
      setActiveTab('select');
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const handleSelectSpec = (id) => {
    setSpecId(id);
    setActiveTab('test');
  };

  const handleTemplateChange = (e) => {
    setSelectedTemplate(e.target.value);
    setTemplateContent(templates[e.target.value]);
    setDryRunResult(null);
    setRunResult(null);
  };

  const handleDryRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/dry_run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ template: templateContent, target_base: `http://127.0.0.1:9001` }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Error: ${response.statusText} - ${errorData.detail}`);
      }
      const data = await response.json();
      setDryRunResult(data);
      setActiveTab('results');
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const handleRunTest = async () => {
    setLoading(true);
    setError(null);
    try {
      const isDestructive = selectedTemplate.includes('bola') || selectedTemplate.includes('idor') || selectedTemplate.includes('jwt');
      if (isDestructive && !consent) {
        setError('Consent is required to run destructive tests.');
        setLoading(false);
        return;
      }
      const response = await fetch(`${API_BASE_URL}/run_template`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          spec_id: specId,
          template: templateContent,
          target_base: `http://127.0.0.1:9001`,
          consent: isDestructive
        }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Error: ${response.statusText} - ${errorData.detail}`);
      }
      const data = await response.json();
      setRunResult(data);
      setActiveTab('results');
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  // New functions for reconnaissance and reporting
  const startReconnaissance = async () => {
    setReconLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/spiderfoot/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          target: reconTarget,
          scan_type: "web" 
        }),
      });
      
      const data = await response.json();
      if (data.scan_id) {
        setReconScanId(data.scan_id);
        // Start polling for results
        pollReconResults(data.scan_id);
      } else {
        setError(data.error || 'Failed to start reconnaissance');
        setReconLoading(false);
      }
    } catch (err) {
      setError('Reconnaissance failed: ' + err.message);
      setReconLoading(false);
    }
  };

  const pollReconResults = async (scanId) => {
    let attempts = 0;
    const maxAttempts = 30;
    
    const poll = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/spiderfoot/scan/${scanId}`);
        const data = await response.json();
        
        if (data.status === 'completed') {
          setReconResults(data);
          setReconLoading(false);
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 3000);
        } else {
          setError('Reconnaissance scan timed out');
          setReconLoading(false);
        }
      } catch (err) {
        setError('Failed to fetch reconnaissance results');
        setReconLoading(false);
      }
    };
    
    poll();
  };

  const generateReport = async (format = 'html') => {
    setGeneratingReport(true);
    try {
      const response = await fetch(`${API_BASE_URL}/generate-report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          test_results: runResult || dryRunResult,
          target_url: `http://127.0.0.1:9001`,
          template_used: selectedTemplate,
          report_format: format
        }),
      });
      
      const data = await response.json();
      setReportData(data);
      
      if (format === 'html' && data.html_content) {
        const newWindow = window.open();
        newWindow.document.write(data.html_content);
        newWindow.document.close();
      }
      
    } catch (err) {
      setError('Failed to generate report: ' + err.message);
    } finally {
      setGeneratingReport(false);
    }
  };

  // Helper functions for template display
  const getTemplateDisplayName = (templateKey) => {
    const nameMap = {
      'bola_update.yaml': 'BOLA - UPDATE',
      'graphql_introspect.yaml': 'GraphQL Introspection',
      'idor_read.yaml': 'IDOR - READ', 
      'jwt_reuse.yaml': 'JWT Reuse'
    };
    return nameMap[templateKey] || templateKey.replace('.yaml', '').replace('_', ' ').toUpperCase();
  };

  const getTemplateDescription = (templateKey) => {
    const descMap = {
      'bola_update.yaml': 'Tests for Broken Object Level Authorization by attempting to update another user\'s resources.',
      'graphql_introspect.yaml': 'Performs GraphQL schema introspection to discover available types and fields.',
      'idor_read.yaml': 'Tests for Insecure Direct Object Reference vulnerabilities by accessing other users\' data.',
      'jwt_reuse.yaml': 'Tests JWT token security by reusing tokens across different user contexts.'
    };
    return descMap[templateKey] || 'Security test template';
  };

  const isDestructive = selectedTemplate.includes('bola') || selectedTemplate.includes('idor') || selectedTemplate.includes('jwt');

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 text-white p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <header className="text-center mb-8 slide-in">
          <div className="floating mb-4">
            <h1 className="text-5xl font-bold gradient-text mb-2">SwarmHive</h1>
          </div>
          <p className="text-xl text-gray-300">Advanced API Security Testing Platform</p>
          <div className="w-24 h-1 bg-gradient-to-r from-indigo-500 to-purple-500 mx-auto rounded-full mt-4"></div>
        </header>

        {/* External Reconnaissance Section */}
        <section className="glass-effect p-6 rounded-xl mb-8">
          <h2 className="text-2xl font-bold text-blue-400 mb-4">🕵️ External Reconnaissance</h2>
          <div className="flex space-x-4 items-end">
            <div className="flex-1">
              <label className="block text-gray-300 mb-2">Target Domain</label>
              <input
                type="text"
                placeholder="example.com"
                value={reconTarget}
                onChange={(e) => setReconTarget(e.target.value)}
                className="input-field"
              />
            </div>
            <button
              onClick={startReconnaissance}
              disabled={reconLoading || !reconTarget}
              className="btn-primary px-6 py-3"
            >
              {reconLoading ? 'Scanning...' : 'Start Recon'}
            </button>
          </div>
          
          {reconScanId && (
            <div className="mt-4 p-4 bg-blue-900/20 rounded-lg">
              <p className="text-blue-300">Scan ID: {reconScanId}</p>
              <p className="text-blue-200 text-sm">Reconnaissance in progress...</p>
            </div>
          )}
          
          {reconResults && (
            <div className="mt-4 p-4 bg-green-900/20 rounded-lg">
              <h3 className="text-green-400 font-bold mb-2">Reconnaissance Complete!</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div className="text-center">
                  <p className="text-green-300 font-bold">{reconResults.summary?.subdomains_found || 0}</p>
                  <p className="text-green-200">Subdomains</p>
                </div>
                <div className="text-center">
                  <p className="text-green-300 font-bold">{reconResults.summary?.open_ports || 0}</p>
                  <p className="text-green-200">Open Ports</p>
                </div>
                <div className="text-center">
                  <p className="text-green-300 font-bold">{reconResults.summary?.technologies_detected || 0}</p>
                  <p className="text-green-200">Technologies</p>
                </div>
                <div className="text-center">
                  <p className="text-green-300 font-bold">{reconResults.summary?.security_issues || 0}</p>
                  <p className="text-green-200">Security Issues</p>
                </div>
              </div>
            </div>
          )}
        </section>

        {/* Navigation Tabs */}
        <div className="glass-effect p-2 rounded-xl mb-8 max-w-4xl mx-auto">
          <div className="flex space-x-2">
            {['upload', 'select', 'test', 'results'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex-1 py-3 px-6 rounded-lg font-semibold transition-all ${
                  activeTab === tab
                    ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg'
                    : 'text-gray-400 hover:text-white hover:bg-gray-700'
                }`}
              >
                {tab === 'upload' && '1. Upload'}
                {tab === 'select' && '2. Select'}
                {tab === 'test' && '3. Test'}
                {tab === 'results' && '4. Results'}
              </button>
            ))}
          </div>
        </div>

        <div className="max-w-4xl mx-auto space-y-8">
          {/* Upload Section */}
          {activeTab === 'upload' && (
            <section className="glass-effect p-8 rounded-2xl shadow-2xl slide-in">
              <h2 className="text-3xl font-bold mb-6 gradient-text">1. Upload API Specification</h2>
              <div className="space-y-6">
                <div>
                  <label className="block text-gray-300 text-lg font-medium mb-3">
                    OpenAPI/Swagger Specification URL
                  </label>
                  <div className="flex space-x-4">
                    <input
                      type="text"
                      placeholder="http://127.0.0.1:9001/openapi.json"
                      value={targetUrl}
                      onChange={(e) => setTargetUrl(e.target.value)}
                      className="input-field flex-1"
                    />
                    <button
                      onClick={handleUpload}
                      disabled={loading || !targetUrl}
                      className="btn-primary px-8"
                    >
                      {loading ? 'Uploading...' : 'Upload'}
                    </button>
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* Select Section */}
          {activeTab === 'select' && (
            <section className="glass-effect p-8 rounded-2xl shadow-2xl slide-in">
              <h2 className="text-3xl font-bold mb-6 gradient-text">2. Select Specification & Template</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-4">
                  <label className="block text-gray-300 text-lg font-medium">Available Specifications</label>
                  <select
                    value={specId}
                    onChange={(e) => handleSelectSpec(e.target.value)}
                    className="input-field"
                  >
                    <option value="">Select a specification...</option>
                    {specs.map((spec) => (
                      <option key={spec.spec_id} value={spec.spec_id}>
                        {spec.title || 'Untitled Spec'} ({spec.spec_id.substring(0, 8)})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-4">
                  <label className="block text-gray-300 text-lg font-medium">Security Test Templates</label>
                  <select
                    value={selectedTemplate}
                    onChange={handleTemplateChange}
                    className="input-field"
                  >
                    {Object.keys(templates).map((key) => (
                      <option key={key} value={key}>
                        {getTemplateDisplayName(key)}
                      </option>
                    ))}
                  </select>
                  
                  {/* Template Information */}
                  {selectedTemplate && (
                    <div className={`p-4 rounded-lg ${
                      isDestructive ? 'bg-red-900/20 border border-red-700' : 'bg-blue-900/20 border border-blue-700'
                    }`}>
                      <div className="flex items-start space-x-3">
                        <div className={`w-3 h-3 rounded-full mt-1 flex-shrink-0 ${
                          isDestructive ? 'bg-red-500 animate-pulse' : 'bg-blue-500'
                        }`}></div>
                        <div>
                          <h4 className={`font-bold text-lg ${
                            isDestructive ? 'text-red-300' : 'text-blue-300'
                          }`}>
                            {getTemplateDisplayName(selectedTemplate)}
                          </h4>
                          <p className={`text-sm mt-1 ${
                            isDestructive ? 'text-red-200' : 'text-blue-200'
                          }`}>
                            {getTemplateDescription(selectedTemplate)}
                            {isDestructive && (
                              <span className="block mt-1 font-semibold">
                                ⚠️ Destructive Test - Requires Consent
                              </span>
                            )}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </section>
          )}

          {/* Test Section */}
          {activeTab === 'test' && (
            <section className="glass-effect p-8 rounded-2xl shadow-2xl slide-in">
              <h2 className="text-3xl font-bold mb-6 gradient-text">3. Configure & Execute Test</h2>
              <div className="space-y-6">
                <div>
                  <label className="block text-gray-300 text-lg font-medium mb-3">
                    Test Template Configuration - {selectedTemplate && getTemplateDisplayName(selectedTemplate)}
                  </label>
                  <textarea
                    className="w-full h-80 p-4 code-block rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 custom-scrollbar"
                    value={templateContent}
                    onChange={(e) => setTemplateContent(e.target.value)}
                    spellCheck="false"
                  />
                </div>

                {isDestructive && (
                  <div className="bg-red-900/20 border border-red-700 rounded-xl p-4">
                    <div className="flex items-start space-x-3">
                      <input
                        type="checkbox"
                        id="consent"
                        checked={consent}
                        onChange={(e) => setConsent(e.target.checked)}
                        className="mt-1 w-5 h-5 text-red-600 bg-gray-800 border-red-600 rounded focus:ring-red-500 focus:ring-2"
                      />
                      <div>
                        <label htmlFor="consent" className="text-red-300 font-semibold text-lg block mb-2">
                          ⚠️ Destructive Test Consent Required
                        </label>
                        <p className="text-red-200 text-sm">
                          This test may modify or delete data on the target system. 
                          By checking this box, you confirm you have explicit permission 
                          to run destructive tests on the target environment.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex space-x-4">
                  <button
                    onClick={handleDryRun}
                    disabled={loading || !templateContent}
                    className="btn-secondary flex-1 py-4"
                  >
                    Dry Run
                  </button>
                  <button
                    onClick={handleRunTest}
                    disabled={loading || !specId || !templateContent || (isDestructive && !consent)}
                    className="btn-primary flex-1 py-4"
                  >
                    {loading ? 'Running...' : 'Run Security Test'}
                  </button>
                </div>
              </div>
            </section>
          )}

          {/* Results Section */}
          {activeTab === 'results' && (
            <section className="glass-effect p-8 rounded-2xl shadow-2xl slide-in">
              <h2 className="text-3xl font-bold mb-6 gradient-text">4. Test Results</h2>
              
              {error && (
                <div className="bg-red-900/30 border border-red-700 rounded-xl p-4 mb-6">
                  <div className="flex items-center">
                    <div className="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center mr-3">
                      <span className="text-white text-sm font-bold">!</span>
                    </div>
                    <h3 className="text-xl font-bold text-red-300">Error</h3>
                  </div>
                  <p className="text-red-200 mt-2 pl-9">{error}</p>
                </div>
              )}

              {dryRunResult && (
                <div className="bg-blue-900/30 border border-blue-700 rounded-xl p-6 mb-6">
                  <h3 className="text-xl font-bold text-blue-300 mb-4">Dry Run Preview</h3>
                  <pre className="code-block p-4 rounded-lg overflow-x-auto custom-scrollbar">
                    {JSON.stringify(dryRunResult, null, 2)}
                  </pre>
                </div>
              )}

              {runResult && (
                <div className="space-y-6">
                  {runResult.findings && runResult.findings.length > 0 ? (
                    <div className="bg-red-900/30 border border-red-700 rounded-xl p-6">
                      <div className="flex items-center mb-4">
                        <div className="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center mr-3">
                          <span className="text-white font-bold">!</span>
                        </div>
                        <h3 className="text-2xl font-bold text-red-300">Vulnerabilities Found!</h3>
                      </div>
                      <div className="space-y-4">
                        {runResult.findings.map((finding, index) => (
                          <div key={index} className={`p-4 rounded-lg ${
                            finding.severity === 'high' ? 'finding-high' : 
                            finding.severity === 'medium' ? 'finding-medium' : 
                            finding.severity === 'low' ? 'finding-low' : 'finding-info'
                          }`}>
                            <div className="flex items-center justify-between mb-2">
                              <span className={`font-bold text-lg ${
                                finding.severity === 'high' ? 'text-red-400' : 
                                finding.severity === 'medium' ? 'text-yellow-400' : 
                                finding.severity === 'low' ? 'text-blue-400' : 'text-gray-400'
                              }`}>
                                {finding.type}
                              </span>
                              <span className={`px-3 py-1 rounded-full text-sm font-bold ${
                                finding.severity === 'high' ? 'text-red-400' : 
                                finding.severity === 'medium' ? 'text-yellow-400' : 
                                finding.severity === 'low' ? 'text-blue-400' : 'text-gray-400'
                              } bg-gray-800`}>
                                {finding.severity?.toUpperCase() || 'INFO'}
                              </span>
                            </div>
                            <p className="text-gray-300">{finding.description}</p>
                            {finding.evidence && (
                              <div className="bg-gray-900 rounded p-3 mt-3">
                                <span className="text-gray-400 text-sm font-medium">Evidence:</span>
                                <pre className="text-sm text-gray-300 mt-1 overflow-x-auto custom-scrollbar">
                                  {JSON.stringify(finding.evidence, null, 2)}
                                </pre>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="bg-green-900/30 border border-green-700 rounded-xl p-6">
                      <div className="flex items-center">
                        <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center mr-3">
                          <span className="text-white font-bold">✓</span>
                        </div>
                        <h3 className="text-2xl font-bold text-green-300">No Vulnerabilities Found</h3>
                      </div>
                      <p className="text-green-200 mt-2">The security test completed successfully and no issues were detected.</p>
                    </div>
                  )}
                </div>
              )}

              {/* Report Generation Section */}
              {(runResult || dryRunResult) && (
                <div className="mt-6 p-4 bg-gray-800 rounded-lg">
                  <h3 className="text-xl font-bold text-green-400 mb-4">📊 Generate Security Report</h3>
                  <div className="flex space-x-4">
                    <button
                      onClick={() => generateReport('html')}
                      disabled={generatingReport}
                      className="btn-primary flex-1"
                    >
                      {generatingReport ? 'Generating...' : '📄 Generate HTML Report'}
                    </button>
                    <button
                      onClick={() => generateReport('json')}
                      disabled={generatingReport}
                      className="btn-secondary flex-1"
                    >
                      {generatingReport ? 'Generating...' : '📊 Generate JSON Report'}
                    </button>
                  </div>
                  
                  {reportData && (
                    <div className="mt-4 p-4 bg-green-900/20 rounded-lg">
                      <h4 className="text-green-300 font-semibold">Report Generated Successfully!</h4>
                      <p className="text-green-200 text-sm">
                        Security Score: {reportData.report_data?.executive_summary?.security_score}/100
                      </p>
                    </div>
                  )}
                </div>
              )}
            </section>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;