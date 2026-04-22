# PHANTOM - Next-Generation Security AI

<div align="center">

![PHANTOM](https://img.shields.io/badge/PHANTOM-v2.0.6-00ff41?style=for-the-badge&labelColor=0a0a0a)
![Python](https://img.shields.io/badge/Python-3.8+-3776ab?style=for-the-badge&logo=python&logoColor=ffd43b)
![License](https://img.shields.io/badge/License-MIT-00ff41?style=for-the-badge&labelColor=0a0a0a)

**"What you can't see can still compromise you."**

PHANTOM is a next-generation LLM AI assistant designed for **cybersecurity education and research**. It combines five specialized thinking engines that reason through complex security problems before delivering authoritative answers.

</div>

---

## Quick Start (No Setup!)

```bash
# Just run this - works immediately!
python phantom.py
```

PHANTOM auto-installs dependencies and auto-detects LLM backends. Run it anywhere:

```bash
# On your local machine
python phantom.py

# On Kali Linux
python phantom.py

# On Termux (Android)
python phantom.py

# Ask a question directly
python phantom.py "How does SQL injection work?"
```

---

## What Makes PHANTOM Different

### Five Thinking Engines

| Engine | Purpose |
|--------|---------|
| **Chain-of-Thought** | Step-by-step linear reasoning |
| **Parallel Thinking** | Red/Blue/Researcher perspectives |
| **Devil's Advocate** | Critical flaw detection |
| **Meta-Cognition** | Self-awareness & knowledge gaps |
| **Red Team** | Adversarial stress testing |

### Zero Setup Required

- ✅ Auto-installs dependencies on first run
- ✅ Auto-detects LLM backends
- ✅ Works offline with demo mode
- ✅ No configuration files needed
- ✅ Runs on any Python 3.8+ system

---

## Usage

### Interactive Mode

```bash
python phantom.py
```

```
PHANTOM▶ How do I exploit SQL injection?
PHANTOM▶ Explain CVE-2024-21762
PHANTOM▶ /search sql injection tutorial
PHANTOM▶ /yt https://youtube.com/watch?v=...
```

### Single Query Mode

```bash
python phantom.py "What is XSS attack?"
```

### Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/clear` | Clear screen |
| `/quit` | Exit PHANTOM |
| `/think fast` | Quick response |
| `/think deep` | Deep analysis (default) |
| `/think paranoid` | Maximum analysis |
| `/search <query>` | Web search |
| `/cve <id>` | CVE lookup |
| `/yt <url>` | YouTube analysis |
| `/run python <code>` | Execute Python |
| `/generate <lang> <desc>` | Generate code |
| `/do <task>` | Autonomous task |
| `/research <topic>` | Deep research |

---

## LLM Backends

PHANTOM auto-detects and prioritizes backends:

### 1. Ollama (Recommended - Free & Local)
```bash
# Install
curl -fsSL https://ollama.ai | sh
ollama pull llama3

# Run PHANTOM - automatically uses Ollama
python phantom.py
```

### 2. Groq (Free Cloud Tier)
```bash
export GROQ_API_KEY="your-key-from-console.groq.com"
python phantom.py
```

### 3. OpenAI (GPT-4o)
```bash
export OPENAI_API_KEY="sk-..."
python phantom.py
```

### 4. Anthropic (Claude 3.5)
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python phantom.py
```

---

## Core Capabilities

### Security Expertise
- **Penetration Testing** - Methodology, tools, techniques
- **CVE Analysis** - Real-time vulnerability lookup
- **Network Reconnaissance** - nmap, Shodan, OSINT
- **Web Application Security** - OWASP Top 10
- **Cryptography** - Encoding, encryption, hashing
- **CTF Challenges** - Hints, techniques, walkthroughs
- **Malware Analysis** - Static/dynamic analysis basics
- **Cloud Security** - AWS, Azure, GCP security

### Autonomous Capabilities
- **Code Generation** - Produces working code on demand
- **Self-Learning** - Learns from every interaction
- **YouTube Learning** - Extracts knowledge from videos
- **Deep Research** - Synthesizes information from sources
- **Code Execution** - Runs code safely in sandbox

### Demo Mode (No LLM)

Even without an LLM backend, PHANTOM provides:
- SQL Injection examples & prevention
- XSS attacks & defenses
- Nmap scanning commands
- Metasploit framework usage
- CVE lookup guidance
- Network security concepts

---

## Examples

### SQL Injection Analysis
```
PHANTOM▶ How do I prevent SQL injection in Python?
```
Returns: Attack examples, vulnerable vs. safe code, prevention techniques

### CVE Lookup
```
PHANTOM▶ What is CVE-2024-21762?
```
Returns: Description, severity, affected systems, mitigation

### Code Generation
```
PHANTOM▶ /generate python sql injection checker
```
Returns: Complete working Python script

### CTF Challenge Help
```
PHANTOM▶ I'm stuck on a buffer overflow challenge
```
Returns: Explanation, approach hints, techniques to try

---

## Security Notice

⚠️ **PHANTOM is for authorized security research and education only.**

Always:
- ✅ Obtain proper authorization before testing
- ✅ Follow responsible disclosure practices
- ✅ Use only on systems you own or have permission to test
- ✅ Practice on CTF platforms and labs
- ✅ Study and learn security concepts

Never:
- ❌ Use for unauthorized access
- ❌ Attack systems without permission
- ❌ Share techniques for malicious purposes

---

## Installation

### Option 1: Direct Run (Recommended)
```bash
git clone https://github.com/Njap-png/Cogitrongit.git
cd Cogitrongit
python phantom.py
```

### Option 2: Install as Package
```bash
pip install -e .
phantom
```

### Option 3: Docker
```bash
docker run -it ghcr.io/njap-png/cogitrongit/phantom:latest
```

---

## Project Structure

```
phantom/
├── phantom.py              # Main entry point (standalone)
├── core/
│   ├── llm.py            # LLM backend abstraction
│   ├── thinking.py         # Five thinking engines
│   ├── soul.py            # Personality system
│   ├── learner.py          # Self-learning engine
│   ├── agents.py           # Autonomous agents
│   ├── sandbox.py         # Safe code execution
│   └── youtube.py         # Video learning
├── tools/
│   ├── decoder.py         # 20+ encoding formats
│   ├── web_search.py       # Multi-engine search
│   └── web_crawler.py     # Site crawling
└── requirements.txt
```

---

## Requirements

- Python 3.8+
- rich (auto-installed)
- requests (auto-installed)
- beautifulsoup4 (auto-installed)
- duckduckgo-search (auto-installed)

---

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## License

MIT License - See [LICENSE](LICENSE)

---

<div align="center">

**PHANTOM v2.0.6-OMEGA** — Next-Generation Security AI

Built with Five Thinking Engines for Deep Reasoning

*What you can't see can still compromise you.*

**[Get Started →](#quick-start-zero-setup)**

</div>