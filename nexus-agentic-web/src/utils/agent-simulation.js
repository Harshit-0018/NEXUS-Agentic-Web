/**
 * NEXUS — Agent Simulation Engine
 * Simulates realistic agent execution with step-by-step logs,
 * browser URL updates, and structured output generation.
 */

const AgentSimulator = (() => {
  let running = false;
  let stopRequested = false;
  let stepCount = 0;
  let startTime = null;

  // ─── Step templates by task type ───────────────────────────────────────────
  const STEP_PROFILES = {
    research: [
      { type: 'think',   icon: '🧠', label: 'PLANNING',   text: 'Analyzing task and decomposing into subtasks: <strong>search → filter → extract → structure</strong>' },
      { type: 'browse',  icon: '🌐', label: 'NAVIGATE',   text: 'Opening search engine to find relevant sources', url: 'https://www.google.com/search?q=...' },
      { type: 'extract', icon: '📋', label: 'EXTRACT',    text: 'Found <strong>23 search results</strong>. Filtering for relevance and recency...' },
      { type: 'browse',  icon: '🌐', label: 'NAVIGATE',   text: 'Following top result to primary source', url: 'https://techcrunch.com/...' },
      { type: 'extract', icon: '📋', label: 'EXTRACT',    text: 'Extracting structured data: names, amounts, dates, investors...' },
      { type: 'browse',  icon: '🌐', label: 'NAVIGATE',   text: 'Cross-referencing with second source for accuracy', url: 'https://crunchbase.com/...' },
      { type: 'action',  icon: '⚡', label: 'EXECUTE',    text: 'Cross-referencing data across <strong>4 sources</strong>. Resolving conflicts...' },
      { type: 'think',   icon: '🧠', label: 'REASONING',  text: 'Confidence check: <strong>94%</strong> data consistency across sources. Proceeding.' },
      { type: 'extract', icon: '📋', label: 'STRUCTURE',  text: 'Converting raw data into structured JSON format with schema validation' },
      { type: 'think',   icon: '🧠', label: 'VERIFY',     text: 'Final verification pass. All fields populated. Quality score: <strong>97/100</strong>' },
      { type: 'done',    icon: '✅', label: 'COMPLETE',   text: 'Task completed successfully. Output formatted and ready.' },
    ],
    travel: [
      { type: 'think',   icon: '🧠', label: 'PLANNING',   text: 'Breaking down travel search: <strong>flights → hotels → visa → itinerary</strong>' },
      { type: 'browse',  icon: '🌐', label: 'NAVIGATE',   text: 'Opening flight search aggregator', url: 'https://www.google.com/flights' },
      { type: 'action',  icon: '⚡', label: 'INTERACT',   text: 'Entering departure city, destination, and date range into search form' },
      { type: 'extract', icon: '📋', label: 'EXTRACT',    text: 'Found <strong>47 flight options</strong>. Applying budget filter: under $800...' },
      { type: 'browse',  icon: '🌐', label: 'NAVIGATE',   text: 'Checking alternate booking platform for price comparison', url: 'https://www.skyscanner.com/...' },
      { type: 'think',   icon: '🧠', label: 'COMPARE',    text: 'Analyzing: layovers, airlines, total travel time, baggage policies...' },
      { type: 'action',  icon: '⚡', label: 'RECOVER',    text: 'One result showed outdated price. Re-fetching with live pricing API.' },
      { type: 'extract', icon: '📋', label: 'STRUCTURE',  text: 'Ranking <strong>top 5 options</strong> by value score (price + duration + comfort)' },
      { type: 'done',    icon: '✅', label: 'COMPLETE',   text: 'Flight search complete. Best options identified with full details.' },
    ],
    shopping: [
      { type: 'think',   icon: '🧠', label: 'PLANNING',   text: 'Price comparison strategy: <strong>Amazon → Flipkart → Croma → eBay</strong>' },
      { type: 'browse',  icon: '🌐', label: 'NAVIGATE',   text: 'Opening Amazon product search', url: 'https://www.amazon.in/s?k=...' },
      { type: 'extract', icon: '📋', label: 'EXTRACT',    text: 'Found product. Extracting: price ₹1,29,900, rating 4.5★, seller: Amazon' },
      { type: 'browse',  icon: '🌐', label: 'NAVIGATE',   text: 'Checking Flipkart listing', url: 'https://www.flipkart.com/...' },
      { type: 'extract', icon: '📋', label: 'EXTRACT',    text: 'Flipkart price: ₹1,24,999. Checking exchange offers and bank discounts...' },
      { type: 'action',  icon: '⚡', label: 'INTERACT',   text: 'Applying HDFC bank offer filter. Additional ₹5,000 discount detected!' },
      { type: 'browse',  icon: '🌐', label: 'NAVIGATE',   text: 'Verifying Croma availability', url: 'https://www.croma.com/...' },
      { type: 'think',   icon: '🧠', label: 'ANALYZE',    text: 'Calculating total cost including EMI, delivery, and warranty across all platforms.' },
      { type: 'done',    icon: '✅', label: 'COMPLETE',   text: 'Price comparison done. Best deal identified with breakdown.' },
    ],
    news: [
      { type: 'think',   icon: '🧠', label: 'PLANNING',   text: 'Query strategy: <strong>official blog → tech news → press releases → Twitter</strong>' },
      { type: 'browse',  icon: '🌐', label: 'NAVIGATE',   text: 'Checking Azure official blog for announcements', url: 'https://azure.microsoft.com/blog' },
      { type: 'extract', icon: '📋', label: 'EXTRACT',    text: 'Found <strong>12 Azure AI posts</strong> from past 7 days. Filtering for significance...' },
      { type: 'browse',  icon: '🌐', label: 'NAVIGATE',   text: 'Cross-checking tech news coverage', url: 'https://www.theverge.com/...' },
      { type: 'extract', icon: '📋', label: 'EXTRACT',    text: 'Extracting key announcements: GPT-4o integration, new pricing tiers, SDK updates...' },
      { type: 'think',   icon: '🧠', label: 'SUMMARIZE',  text: 'Deduplicating stories across sources. Generating importance ranking...' },
      { type: 'done',    icon: '✅', label: 'COMPLETE',   text: 'News summary compiled. 7 distinct updates found.' },
    ],
    default: [
      { type: 'think',   icon: '🧠', label: 'PLANNING',   text: 'Analyzing goal and creating execution plan with <strong>chain-of-thought reasoning</strong>.' },
      { type: 'browse',  icon: '🌐', label: 'NAVIGATE',   text: 'Agent initiating browser session and navigating to relevant URL', url: 'https://www.google.com' },
      { type: 'extract', icon: '📋', label: 'EXTRACT',    text: 'Parsing DOM structure and identifying relevant data elements...' },
      { type: 'action',  icon: '⚡', label: 'EXECUTE',    text: 'Executing interaction: clicking elements, filling forms, scrolling...' },
      { type: 'think',   icon: '🧠', label: 'EVALUATE',   text: 'Evaluating results against original goal. Adjusting plan if needed.' },
      { type: 'extract', icon: '📋', label: 'STRUCTURE',  text: 'Structuring extracted data. Applying output schema validation.' },
      { type: 'done',    icon: '✅', label: 'COMPLETE',   text: 'Task completed. All objectives satisfied.' },
    ]
  };

  // ─── Result templates ───────────────────────────────────────────────────────
  const RESULTS = {
    research: `<span class="highlight">// Research Results — AI Startups Funded in 2024</span>
<span class="key">[
  {</span>
    <span class="key">"rank":</span> <span class="val">1</span>,
    <span class="key">"name":</span> <span class="val">"Cognition AI"</span>,
    <span class="key">"funding":</span> <span class="val">"$175M Series A"</span>,
    <span class="key">"founders":</span> <span class="val">["Scott Wu", "Steven Hao", "Walden Yan"]</span>,
    <span class="key">"investors":</span> <span class="val">["Founders Fund", "Stripe", "Jensen Huang"]</span>,
    <span class="key">"focus":</span> <span class="val">"Autonomous software engineering"</span>
  <span class="key">},
  {</span>
    <span class="key">"rank":</span> <span class="val">2</span>,
    <span class="key">"name":</span> <span class="val">"Mistral AI"</span>,
    <span class="key">"funding":</span> <span class="val">"$1.1B (combined rounds)"</span>,
    <span class="key">"founders":</span> <span class="val">["Arthur Mensch", "Guillaume Lample"]</span>,
    <span class="key">"investors":</span> <span class="val">["a16z", "General Catalyst", "Lightspeed"]</span>,
    <span class="key">"focus":</span> <span class="val">"Open-source frontier LLMs"</span>
  <span class="key">},
  {</span>
    <span class="key">"rank":</span> <span class="val">3</span>,
    <span class="key">"name":</span> <span class="val">"xAI (Grok)"</span>,
    <span class="key">"funding":</span> <span class="val">"$6B"</span>,
    <span class="key">"founders":</span> <span class="val">["Elon Musk"]</span>,
    <span class="key">"investors":</span> <span class="val">["Andreessen Horowitz", "Sequoia Capital"]</span>,
    <span class="key">"focus":</span> <span class="val">"Real-time AI with X integration"</span>
  <span class="key">},
  {</span>
    <span class="key">"rank":</span> <span class="val">4</span>,
    <span class="key">"name":</span> <span class="val">"Harvey AI"</span>,
    <span class="key">"funding":</span> <span class="val">"$100M Series B"</span>,
    <span class="key">"investors":</span> <span class="val">["Sequoia", "Google Ventures", "OpenAI"]</span>,
    <span class="key">"focus":</span> <span class="val">"LLMs for legal workflows"</span>
  <span class="key">},
  {</span>
    <span class="key">"rank":</span> <span class="val">5</span>,
    <span class="key">"name":</span> <span class="val">"Imbue"</span>,
    <span class="key">"funding":</span> <span class="val">"$200M Series B"</span>,
    <span class="key">"investors":</span> <span class="val">["Astera Institute", "Nvidia", "Intel"]</span>,
    <span class="key">"focus":</span> <span class="val">"Reasoning-first AI agents"</span>
  <span class="key">}
]</span>

<span class="highlight">// Metadata</span>
Steps used: 11 | Sources: 4 | Confidence: 97%`,

    travel: `<span class="highlight">// Flight Search Results — DEL → JFK (Round-Trip)</span>

<span class="key">TOP OPTIONS (under $800, sorted by value score):</span>

<span class="val">1. Air India AI-101 + AI-102</span>
   Outbound: DEL → JFK | 14h 30m | Non-stop
   Return:   JFK → DEL | 15h 10m | Non-stop
   Price:    <span class="highlight">$742 (BEST DEAL)</span>
   Airline:  Air India | Rating: 3.8★

<span class="val">2. Emirates EK-507 + EK-510</span>
   Outbound: DEL → DXB → JFK | 18h 45m | 1 stop
   Price:    <span class="highlight">$681</span> (with HDFC discount)
   Note:     4h layover in Dubai. Lounge access included.

<span class="val">3. Qatar Airways QR-574 + QR-571</span>
   Outbound: DEL → DOH → JFK | 17h 55m | 1 stop
   Price:    <span class="highlight">$709</span>
   Note:     Highly rated service. 2h layover in Doha.

<span class="highlight">Recommendation:</span> Option 2 (Emirates) offers best price with comfortable layover.
Steps used: 9 | Platforms checked: 3 | Live prices verified: ✓`,

    shopping: `<span class="highlight">// iPhone 16 Pro — Price Comparison</span>

Platform     Price        Offer                    Final Price
─────────────────────────────────────────────────────────────
Amazon       ₹1,29,900   No current bank offer    <span class="val">₹1,29,900</span>
Flipkart     ₹1,24,999   HDFC -₹5,000             <span class="highlight">₹1,19,999 ★ BEST</span>
Croma        ₹1,31,000   Exchange up to -₹15,000  ₹1,16,000 (w/exchange)

<span class="highlight">RECOMMENDATION:</span>
→ <span class="val">Flipkart</span> has the lowest base price at ₹1,19,999 with HDFC card.
→ If you have an old phone to exchange, <span class="val">Croma</span> could be better.
→ All three offer 1-year Apple warranty + same-day delivery.

<span class="highlight">Savings vs MRP (₹1,34,900):</span> Up to ₹14,901 (11%)
Steps used: 9 | Price checks: 3 | Offers verified: 5`,

    news: `<span class="highlight">// Microsoft Azure AI Updates — Last 7 Days</span>

<span class="val">1. GPT-4o Mini Now GA on Azure OpenAI</span>
   Azure confirmed general availability of GPT-4o Mini.
   50% cheaper than GPT-4o for standard tasks.

<span class="val">2. Azure AI Foundry — New SDK v2.0</span>
   Streamlined agent creation, built-in memory, tool calling.
   Supports MCP protocol natively.

<span class="val">3. Phi-3.5 Family Released</span>
   New small language models optimized for edge deployment.
   Phi-3.5-mini achieves near-GPT-4 performance at 3.8B params.

<span class="val">4. Azure AI Search — Vector + Hybrid Mode</span>
   Combined semantic + keyword search now default in v11.
   50% latency improvement in benchmark tests.

<span class="val">5. Responsible AI Dashboard v2</span>
   New fairness metrics, causal analysis, counterfactual explorer.

Sources: azure.microsoft.com, theverge.com, techcrunch.com
Steps used: 7 | Articles read: 12 | Unique updates: 7`,

    default: `<span class="highlight">// Task Completed Successfully</span>

<span class="key">Result:</span> <span class="val">Agent completed the requested task.</span>

Steps executed: 7
Data sources accessed: 3
Execution time: ~18s
Confidence score: 91%

<span class="highlight">// Full trace available in execution log above.</span>`
  };

  // ─── Utilities ──────────────────────────────────────────────────────────────
  function detectTaskType(task) {
    const t = task.toLowerCase();
    if (t.includes('startup') || t.includes('research') || t.includes('github') || t.includes('company')) return 'research';
    if (t.includes('flight') || t.includes('hotel') || t.includes('travel') || t.includes('trip')) return 'travel';
    if (t.includes('price') || t.includes('buy') || t.includes('iphone') || t.includes('product') || t.includes('shop')) return 'shopping';
    if (t.includes('news') || t.includes('update') || t.includes('latest') || t.includes('azure') || t.includes('microsoft')) return 'news';
    return 'default';
  }

  function elapsed() {
    return ((Date.now() - startTime) / 1000).toFixed(1) + 's';
  }

  function updateStatus(state, text) {
    const dot = document.querySelector('.status-dot');
    const label = document.getElementById('status-text');
    if (dot) { dot.className = 'status-dot ' + state; }
    if (label) label.textContent = text;
  }

  function updateBrowserUrl(url, loading = false) {
    const urlEl = document.getElementById('browser-url');
    const spinner = document.getElementById('browser-loading');
    if (urlEl) urlEl.textContent = url;
    if (spinner) spinner.style.display = loading ? 'inline' : 'none';
  }

  function showBrowserPage(type) {
    const content = document.getElementById('browser-content');
    if (!content) return;

    if (type === 'loading') {
      content.innerHTML = `
        <div class="browser-page">
          <div class="browser-page-skeleton">
            <div class="skeleton-line w80" style="height:14px; margin-bottom: 1rem;"></div>
            <div class="skeleton-line w100"></div>
            <div class="skeleton-line w60"></div>
            <div class="skeleton-line w80"></div>
            <div class="skeleton-line w40"></div>
            <div style="margin-top:1rem; display:flex; gap:0.5rem;">
              <div class="skeleton-line w40" style="height:60px;"></div>
              <div class="skeleton-line w40" style="height:60px;"></div>
            </div>
            <div class="skeleton-line w100" style="margin-top:0.5rem;"></div>
            <div class="skeleton-line w80"></div>
          </div>
        </div>`;
    } else if (type === 'idle') {
      content.innerHTML = `
        <div class="browser-idle-state">
          <div class="idle-icon">
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
              <polygon points="32,4 60,18 60,46 32,60 4,46 4,18" stroke="#00FFB2" stroke-width="1.5" fill="none" opacity="0.5"/>
              <circle cx="32" cy="32" r="8" stroke="#00FFB2" stroke-width="1.5" fill="none"/>
              <circle cx="32" cy="32" r="2" fill="#00FFB2"/>
            </svg>
          </div>
          <p>Agent ready. Awaiting task...</p>
        </div>`;
    }
  }

  function appendStep(step, elapsedTime) {
    const log = document.getElementById('steps-log');
    if (!log) return;

    const empty = log.querySelector('.log-empty');
    if (empty) empty.remove();

    const el = document.createElement('div');
    el.className = `log-step step-${step.type}`;
    el.innerHTML = `
      <div class="step-icon">${step.icon}</div>
      <div class="step-content">
        <div class="step-action-label">${step.label}</div>
        <div class="step-text">${step.text}</div>
      </div>
      <div class="step-time">${elapsedTime}</div>
    `;
    log.appendChild(el);
    log.scrollTop = log.scrollHeight;
  }

  function showResult(taskType) {
    const container = document.getElementById('output-result');
    const body = document.getElementById('result-body');
    if (!container || !body) return;
    body.innerHTML = RESULTS[taskType] || RESULTS.default;
    container.style.display = 'block';
    container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function delay(ms) {
    return new Promise(resolve => {
      const id = setTimeout(resolve, ms);
      // Store for cancellation
      delay._ids = delay._ids || [];
      delay._ids.push(id);
    });
  }

  function clearDelays() {
    if (delay._ids) {
      delay._ids.forEach(id => clearTimeout(id));
      delay._ids = [];
    }
  }

  // ─── Main run function ──────────────────────────────────────────────────────
  async function run(task, maxSteps) {
    if (running) return;
    running = true;
    stopRequested = false;
    startTime = Date.now();
    stepCount = 0;

    const taskType = detectTaskType(task);
    const steps = STEP_PROFILES[taskType] || STEP_PROFILES.default;
    const speedMap = { 'Normal (Visible)': 1400, 'Fast': 700, 'Turbo': 200 };
    const speedSelect = document.getElementById('agent-speed');
    const baseDelay = speedMap[speedSelect?.value] || 1400;

    // Reset UI
    document.getElementById('steps-log').innerHTML = '<div class="log-empty">Initializing agent...</div>';
    document.getElementById('output-result').style.display = 'none';
    updateStatus('running', 'Running');
    updateBrowserUrl('Initializing agent session...', false);
    showBrowserPage('idle');

    await delay(600);

    const stepsToRun = Math.min(steps.length, maxSteps);

    for (let i = 0; i < stepsToRun; i++) {
      if (stopRequested) break;

      const step = steps[i];
      stepCount++;

      // Update browser if navigating
      if (step.type === 'browse' && step.url) {
        updateBrowserUrl(step.url, true);
        showBrowserPage('loading');
        await delay(baseDelay * 0.6);
        if (stopRequested) break;
        updateBrowserUrl(step.url, false);
      }

      appendStep(step, elapsed());
      updateStatus('running', `Step ${stepCount}/${stepsToRun}`);

      await delay(baseDelay + (Math.random() * 300 - 150));
      if (stopRequested) break;
    }

    if (!stopRequested) {
      updateStatus('done', 'Complete');
      updateBrowserUrl('Task completed ✓', false);
      showBrowserPage('idle');
      await delay(400);
      showResult(taskType);
    } else {
      updateStatus('idle', 'Stopped');
      updateBrowserUrl('about:blank', false);
      showBrowserPage('idle');
      appendStep({
        type: 'error', icon: '⛔', label: 'STOPPED',
        text: 'Agent execution stopped by user after ' + stepCount + ' steps.'
      }, elapsed());
    }

    running = false;
  }

  function stop() {
    stopRequested = true;
    clearDelays();
  }

  return { run, stop, isRunning: () => running };
})();
