"""Small dependency-free browser UI served by FastAPI."""

from __future__ import annotations

import json
from html import escape

from .schemas import DEMO_PRINCIPALS


def _demo_options() -> str:
    return "\n".join(
        f'<option value="{escape(name)}">{escape(name)}</option>' for name in DEMO_PRINCIPALS
    )


def _demo_json() -> str:
    return json.dumps({name: principal.model_dump() for name, principal in DEMO_PRINCIPALS.items()})


def render_ui() -> str:
    """Return the minimal query UI without embedding credentials or email bodies."""

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SecureMail RAG</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 820px; margin: 2rem auto; padding: 0 1rem; color: #182230; }}
    .banner {{ background: #fff3cd; border: 1px solid #e0b84c; border-radius: .5rem; padding: .8rem 1rem; }}
    label {{ display: block; margin-top: .8rem; font-weight: 600; }}
    input, select, textarea, button {{ box-sizing: border-box; width: 100%; padding: .65rem; margin-top: .3rem; font: inherit; }}
    textarea {{ min-height: 7rem; }}
    button {{ margin-top: 1rem; background: #1769aa; color: white; border: 0; border-radius: .4rem; cursor: pointer; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0 1rem; }}
    .result {{ margin-top: 1.5rem; border-top: 1px solid #ccd3dc; padding-top: 1rem; white-space: pre-wrap; }}
    .active {{ font-weight: 700; color: #1769aa; }}
    @media (max-width: 650px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <h1>SecureMail RAG</h1>
  <p class="banner"><strong>Synthetic RBAC demo:</strong> the active principal and
  access policy are created for this experiment. They are not Enron's historical permissions.
  Active principal: <span id="active" class="active">Finance employee</span></p>
  <label for="demo">Demo principal</label>
  <select id="demo">{_demo_options()}</select>
  <div class="grid">
    <div><label for="role">Role</label><input id="role"></div>
    <div><label for="department">Department</label><input id="department"></div>
    <div><label for="access_level">Access level</label><input id="access_level"></div>
    <div><label for="resource_scope">Resource scope</label><input id="resource_scope"></div>
  </div>
  <label for="question">Question</label>
  <textarea id="question" placeholder="Ask about the authorized email evidence..."></textarea>
  <button id="submit">Query securely</button>
  <section id="result" class="result" hidden></section>
  <script>
    const principals = {_demo_json()};
    const demo = document.getElementById('demo');
    const result = document.getElementById('result');
    function syncPrincipal() {{
      const p = principals[demo.value];
      for (const key of ['role', 'department', 'access_level', 'resource_scope']) document.getElementById(key).value = p[key];
      document.getElementById('active').textContent = demo.value;
    }}
    demo.addEventListener('change', syncPrincipal);
    syncPrincipal();
    document.getElementById('submit').addEventListener('click', async () => {{
      result.hidden = false;
      result.textContent = 'Querying...';
      const principal = Object.fromEntries(['role', 'department', 'access_level', 'resource_scope'].map(key => [key, document.getElementById(key).value]));
      const response = await fetch('/query', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{question: document.getElementById('question').value, principal}}) }});
      const data = await response.json();
      if (!response.ok) {{ result.textContent = `Error ${{response.status}}: ${{data.detail || 'request failed'}}`; return; }}
      result.textContent = `Answer:\n${{data.answer}}\n\nSources: ${{data.source_email_ids.join(', ') || 'none'}}\nEvidence items: ${{data.retrieved_evidence_count}}\nRefused/insufficient: ${{data.refused || data.insufficient_evidence ? 'yes' : 'no'}}`;
    }});
  </script>
</body>
</html>"""
