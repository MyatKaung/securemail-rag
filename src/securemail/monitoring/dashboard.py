"""Safe aggregated monitoring dashboard page."""

from __future__ import annotations


def render_dashboard() -> str:
    """Render a dashboard that fetches aggregate metrics, never raw records."""

    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SecureMail RAG Monitoring</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 1000px; margin: 2rem auto; padding: 0 1rem; color: #182230; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 1rem; }
    .card { border: 1px solid #ccd3dc; border-radius: .5rem; padding: 1rem; background: #f8fafc; }
    .value { display: block; font-size: 1.6rem; font-weight: 700; margin-top: .4rem; }
    .chart { margin-top: 1.5rem; border-top: 1px solid #ccd3dc; padding-top: 1rem; }
    .bar { background: #1769aa; color: white; padding: .25rem .5rem; margin: .3rem 0; min-width: 2rem; }
  </style>
</head>
<body>
  <h1>SecureMail RAG Monitoring</h1>
  <p>Aggregated operational metrics only. Request questions, prompts, email bodies,
  API keys, and individual feedback comments are not displayed.</p>
  <div id="metrics" class="grid"></div>
  <div class="chart"><h2>Requests over time</h2><div id="requests"></div></div>
  <script>
    const metricLabels = [
      ['total_requests', 'Total requests', v => v],
      ['average_end_to_end_latency_ms', 'Average end-to-end latency (ms)', v => v.toFixed(1)],
      ['p95_end_to_end_latency_ms', 'P95 end-to-end latency (ms)', v => v.toFixed(1)],
      ['average_retrieval_latency_ms', 'Average retrieval latency (ms)', v => v.toFixed(1)],
      ['average_reranking_latency_ms', 'Average reranking latency (ms)', v => v.toFixed(1)],
      ['average_llm_latency_ms', 'Average LLM latency (ms)', v => v.toFixed(1)],
      ['permission_denials', 'Permission denials', v => v],
      ['refusal_or_insufficient_rate', 'Refusal/insufficient rate', v => (v * 100).toFixed(1) + '%'],
      ['positive_feedback', 'Positive feedback', v => v],
      ['negative_feedback', 'Negative feedback', v => v]
    ];
    async function load() {
      const data = await (await fetch('/monitoring/metrics')).json();
      document.getElementById('metrics').innerHTML = metricLabels.map(([key, label, format]) =>
        `<div class="card">${label}<span class="value">${format(data[key])}</span></div>`).join('');
      const max = Math.max(...data.requests_by_day.map(item => item.count), 1);
      document.getElementById('requests').innerHTML = data.requests_by_day.map(item =>
        `<div>${item.date}<div class="bar" style="width:${Math.max(4, item.count / max * 100)}%">${item.count}</div></div>`).join('') || 'No requests yet.';
    }
    load();
  </script>
</body>
</html>"""
