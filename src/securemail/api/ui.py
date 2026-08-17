"""Small dependency-free browser UI served by FastAPI."""

from __future__ import annotations

from html import escape

from securemail.security import DEMO_IDENTITIES, DemoIdentity


def _demo_options() -> str:
    return "\n".join(
        f'<option value="{escape(identity.email)}">{escape(identity.label)} — '
        f'{escape(identity.email)}</option>'
        for identity in DEMO_IDENTITIES.values()
    )


def render_login() -> str:
    """Return the synthetic demo login page."""

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SecureMail RAG — Login</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 620px; margin: 3rem auto; padding: 0 1rem; color: #182230; }}
    .banner {{ background: #fff3cd; border: 1px solid #e0b84c; border-radius: .5rem; padding: .8rem 1rem; }}
    label {{ display: block; margin-top: 1rem; font-weight: 600; }}
    input, select, button {{ box-sizing: border-box; width: 100%; padding: .65rem; margin-top: .3rem; font: inherit; }}
    button {{ margin-top: 1.2rem; background: #1769aa; color: white; border: 0; border-radius: .4rem; cursor: pointer; }}
    #status {{ margin-top: 1rem; color: #9b1c1c; }}
  </style>
</head>
<body>
  <h1>SecureMail RAG</h1>
  <p class="banner"><strong>Synthetic demo login:</strong> these four accounts,
  passwords, and permissions are created only for this experiment. They are not
  Enron historical accounts or permissions. Demo passwords are documented in
  <code>config/demo_users.yaml</code> and are not production secrets.</p>
  <label for="email">Synthetic demo identity</label>
  <select id="email">{_demo_options()}</select>
  <label for="password">Demo password</label>
  <input id="password" type="password" autocomplete="current-password">
  <button id="login">Log in</button>
  <p id="status" role="alert"></p>
  <script>
    document.getElementById('login').addEventListener('click', async () => {{
      const response = await fetch('/login', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{email: document.getElementById('email').value, password: document.getElementById('password').value}})
      }});
      const data = await response.json();
      if (!response.ok) {{ document.getElementById('status').textContent = data.detail || 'Login failed'; return; }}
      window.location = '/';
    }});
  </script>
</body>
</html>"""


def render_ui(identity: DemoIdentity) -> str:
    """Return the authenticated query UI without embedding credentials or bodies."""

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
    button.feedback {{ width: auto; margin-right: .5rem; background: #4b5563; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0 1rem; }}
    .result {{ margin-top: 1.5rem; border-top: 1px solid #ccd3dc; padding-top: 1rem; white-space: pre-wrap; }}
    .active {{ font-weight: 700; color: #1769aa; }}
    @media (max-width: 650px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <h1>SecureMail RAG</h1>
  <p class="banner"><strong>Synthetic demo identity:</strong> this account and its
  access policy are created for this experiment. They are not an Enron historical
  account or permission.</p>
  <p><strong>Logged in email:</strong> <span class="active">{escape(identity.email)}</span><br>
  <strong>Department:</strong> {escape(identity.principal.department)}<br>
  <strong>Role:</strong> {escape(identity.principal.role)}</p>
  <p><a href="/logout">Log out</a></p>
  <label for="question">Question</label>
  <textarea id="question" placeholder="Ask about the authorized email evidence..."></textarea>
  <button id="submit">Query securely</button>
  <section id="result" class="result" hidden></section>
  <section id="feedback" class="result" hidden>
    <strong>Was this answer useful?</strong>
    <button class="feedback" id="positive">👍 Yes</button>
    <button class="feedback" id="negative">👎 No</button>
    <input id="feedback-comment" maxlength="500" placeholder="Optional short comment">
    <span id="feedback-status"></span>
  </section>
  <script>
    const result = document.getElementById('result');
    const feedback = document.getElementById('feedback');
    let lastRequestId = null;
    document.getElementById('submit').addEventListener('click', async () => {{
      result.hidden = false;
      result.textContent = 'Querying...';
      const response = await fetch('/query', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{question: document.getElementById('question').value}}) }});
      const data = await response.json();
      if (!response.ok) {{ result.textContent = `Error ${{response.status}}: ${{data.detail || 'request failed'}}`; return; }}
      lastRequestId = data.request_id;
      result.textContent = `Answer:\n${{data.answer}}\n\nSources: ${{data.source_email_ids.join(', ') || 'none'}}\nEvidence items: ${{data.retrieved_evidence_count}}\nRefused/insufficient: ${{data.refused || data.insufficient_evidence ? 'yes' : 'no'}}\nRequest ID: ${{data.request_id}}`;
      feedback.hidden = false;
    }});
    async function sendFeedback(positive) {{
      if (!lastRequestId) return;
      const response = await fetch('/feedback', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{request_id: lastRequestId, positive, comment: document.getElementById('feedback-comment').value || null}}) }});
      const data = await response.json();
      document.getElementById('feedback-status').textContent = response.ok ? ' Thanks for the feedback.' : ` Error: ${{data.detail || 'feedback failed'}}`;
    }}
    document.getElementById('positive').addEventListener('click', () => sendFeedback(true));
    document.getElementById('negative').addEventListener('click', () => sendFeedback(false));
  </script>
</body>
</html>"""
