# PHANTOM - Polymorphic Heuristic AI for Network Threat Analysis & Mentoring

<div align="center">

![PHANTOM Logo](https://raw.githubusercontent.com/Njap-png/Cogitrongit/main/phantom-logo.png)

**`v2.0.5-OMEGA`** — *"What you can't see can still compromise you."*

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![LLM Powered](https://img.shields.io/badge/LLM-Protected-AI-purple.svg)]()

**PHANTOM is a next-generation LLM AI assistant** designed for cybersecurity education and research. It combines five specialized thinking engines that reason through complex security problems before delivering authoritative answers.

</div>

---

## What Makes PHANTOM Different

PHANTOM is not just another chatbot — it's a **Purpose-Built Security AI** with:

### Five Thinking Engines
PHANTOM reasons through complex problems using multiple specialized engines before answering:

| Engine | Purpose |
|--------|---------|
| **Chain-of-Thought** | Step-by-step reasoning for complex problems |
| **Parallel Thinking** | Three simultaneous perspectives (Red/Blue/Research) |
| **Devil's Advocate** | Critical analysis and flaw detection |
| **Meta-Cognition** | Self-awareness and knowledge gap identification |
| **Red Team** | Adversarial stress testing of its own conclusions |

### Autonomous Capabilities
- **Self-Learning**: Learns from every interaction
- **Code Generation**: Creates working code on demand
- **Video Learning**: Extracts knowledge from YouTube tutorials
- **Self-Update**: Can modify its own code
- **Sandboxed Execution**: Run code safely in isolation

### Security Focus
- **CVE Intelligence**: Real-time CVE lookup and analysis
- **Exploit Database**: Search ExploitDB and Metasploit
- **ATT&CK Framework**: MITRE ATT&CK technique lookup
- **Shodan Integration**: Host and device reconnaissance
- **Encoding/Decoding**: 20+ formats with auto-detection

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Njap-png/Cogitrongit.git
cd Cogitrongit/phantom

# Install dependencies
pip install -r requirements.txt

# Run PHANTOM
python phantom.py
```

---

## Usage

### Interactive REPL

```bash
python phantom.py
[PHANTOM]▶ How do I exploit SQL injection in Python?
[PHANTOM]▶ Explain CVE-2024-21762
[PHANTOM]▶ /yt search sql injection tutorial
```

### Commands

| Command | Description |
|---------|-------------|
| `/search <query>` | Web search |
| `/yt <url>` | YouTube video analysis |
| `/cve <id>` | CVE lookup |
| `/do <task>` | Autonomous task execution |
| `/run python <code>` | Run code in sandbox |
| `/generate <lang> <desc>` | Generate code |
| `/research <topic>` | Deep research |
| `/think deep` | Set thinking depth |

---

## Architecture

```
phantom/
├── core/
│   ├── llm.py          # LLM backend abstraction
│   ├── thinking.py     # Five thinking engines
│   ├── soul.py         # Personality and emotions
│   ├── learner.py      # Self-learning engine
│   ├── agents.py       # Autonomous agents
│   ├── sandbox.py      # Safe code execution
│   ├── youtube.py      # Video learning
│   └── cli.py          # Shell capabilities
├── tools/
│   ├── decoder.py      # 20+ encoding formats
│   ├── web_search.py   # Multi-engine search
│   └── web_crawler.py  # Site crawling
└── ui/
    └── splash.py       # Terminal UI
```

---

## LLM Backends

PHANTOM auto-detects available LLM providers:

1. **Ollama** (local, free, private) — Best if running
2. **Groq** (cloud, fast, free tier)
3. **OpenAI** (GPT-4o)
4. **Anthropic** (Claude 3.5 Sonnet)
5. **Google Gemini**
6. **OpenRouter** (100+ models, one key)

---

## Security Notice

PHANTOM is designed for **authorized security research, CTF competitions, and education**. Always:
- Obtain proper authorization before testing
- Follow responsible disclosure practices
- Use only on systems you own or have permission to test
- Never use for malicious purposes

---

## License

MIT License — see [LICENSE](LICENSE)

---

<div align="center">

**PHANTOM v2.0.5-OMEGA** — Next-Generation Security AI

*What you can't see can still compromise you.*

</div>