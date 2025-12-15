# Web Access & Tools Design

Web access is standard for modern coding agents (Cursor, Copilot, Codex CLI, etc.). **swesh will have web access** — the only question is implementation:

| Approach | Agent writes web scripts | swesh provides web tools |
|----------|--------------------------|--------------------------|
| Philosophy | Live-SWE-agent style | Standard agent tooling |

## Experiment: With Tools vs Without Tools

### Experiment A: Web Access, No Tools

Agent has internet but must write its own scripts:

```bash
# Agent writes this on the fly
cat << 'EOF' > /tmp/search.py
import requests
from bs4 import BeautifulSoup

def search(query):
    resp = requests.get(f"https://html.duckduckgo.com/html/?q={query}")
    soup = BeautifulSoup(resp.text, 'html.parser')
    for r in soup.select('.result__title'):
        print(r.get_text())

search("python asyncio timeout example")
EOF
pip install requests beautifulsoup4 && python /tmp/search.py
```

**Pros**: Follows Live-SWE-agent philosophy (self-written tools)
**Cons**: Agent spends tokens on boilerplate, may fail on complex pages

---

### Experiment B: Web Access, With Tools

Pre-built tools available as shell commands:

```bash
# Provided by swesh, agent just calls them
websearch "python asyncio timeout example"
browse https://docs.python.org/3/library/asyncio.html
```

**Pros**: Fast, reliable, optimized for token usage
**Cons**: Fixed interface, agent can't customize

---

## Implementation Options

### For "No Tools" (just enable internet)

```yaml
# In sandbox config
environment:
  network: true  # Allow outbound connections
  # Agent can pip install requests, use curl, etc.
```

### For "With Tools" (provide search/browse commands)

```python
# Pre-installed in sandbox container
# /usr/local/bin/websearch
#!/usr/bin/env python3
import sys, os
import requests

API_KEY = os.environ.get("SERPER_API_KEY")
query = " ".join(sys.argv[1:])

resp = requests.post("https://google.serper.dev/search", 
    json={"q": query}, headers={"X-API-KEY": API_KEY})
    
for r in resp.json().get("organic", [])[:5]:
    print(f"- {r['title']}\n  {r['link']}\n  {r['snippet']}\n")
```

---

## Evaluation Plan

| Metric | How to Measure |
|--------|----------------|
| Task completion | Same task, compare success rate |
| Token usage | Count tokens spent on web-related code |
| Time to solution | Wall clock time |
| Error rate | How often web code fails |

### Test Tasks

1. "Fix this Django error" (requires looking up error message)
2. "Update library X to v2.0" (requires checking migration guide)
3. "Add OAuth login" (requires reading docs)

---

## 🚧 Status: Not Implementing Now

This is exploratory. The experiments above should be run once sandboxing is stable.

Priority order:
1. Sandbox mode (in progress)
2. Web access experiments
3. Decide on tools based on results
