# PHANTOM - Polymorphic Heuristic AI for Network Threat Analysis & Mentoring

<div align="center">

![PHANTOM Logo](https://raw.githubusercontent.com/Njap-png/Cogitrongit/main/phantom-logo.png)

**`v2.0.0-OMEGA`** — *"What you can't see can still compromise you."*

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Platforms](https://img.shields.io/badge/Platforms-Linux%20%C2%B7%20macOS%20%C2%B7%20Windows%20%C2%B7%20Termux-yellow.svg)](#supported-platforms)

</div>

---

## Overview

PHANTOM is a next-generation AI assistant designed for cybersecurity education and research. It combines five specialized thinking engines that reason through complex security problems before delivering authoritative answers.

### Core Features

- **Five Thinking Engines** — Chain-of-Thought, Parallel Perspectives, Devil's Advocate, Meta-Cognition, and Red Team stress testing
- **Multi-Backend LLM** — Supports Ollama, Groq, OpenAI, Anthropic, Google Gemini, and OpenRouter
- **Web Intelligence** — Multi-engine search with CVE lookup, Shodan, ExploitDB, and MITRE ATT&CK integration
- **Decode Engine** — 20+ encoding formats with auto-detection and multi-layer decoding
- **Self-Evolution** — Learns from every interaction to improve future responses
- **Cross-Platform** — Runs on Linux, macOS, Windows, Termux, Kali, Parrot, and more

---

## Supported Platforms

| Platform | Status | Notes |
|----------|--------|-------|
| Linux | ✅ Full | All distributions |
| macOS | ✅ Full | Apple Silicon + Intel |
| Windows (WSL) | ✅ Full | Windows Subsystem for Linux |
| Termux/Android | ✅ Full | Minimal install available |
| Kali Linux | ✅ Full | Optimized for pentesting |
| Parrot OS | ✅ Full | Optimized for pentesting |
| BlackArch | ✅ Full | Optimized for pentesting |

---

## Installation

### Quick Install

```bash
git clone https://github.com/Njap-png/Cogitrongit.git
cd Cogitrongit/phantom
chmod +x install.sh
./install.sh
```

### Manual Install

```bash
git clone https://github.com/Njap-png/Cogitrongit.git
cd Cogitrongit/phantom
pip install -r requirements.txt
python phantom.py
```

### Termux (Android)

```bash
pkg update && pkg install python git
git clone https://github.com/Njap-png/Cogitrongit.git
cd Cogitrongit/phantom
./install.sh --minimal
```

---

## Configuration

On first run, PHANTOM will launch a setup wizard:

1. **Select LLM Backend** — Choose from available providers (Ollama, Groq, OpenAI, etc.)
2. **Enter API Key** — Required for cloud backends
3. **Set Thinking Mode** — fast (1 engine), deep (3 engines), or paranoid (5 engines)
4. **Choose Theme** — matrix, dracula, monokai, or blood

Configuration is stored in `~/.phantom/config.yaml`.

---

## Usage

### Commands

| Command | Description |
|---------|-------------|
| `/search <query>` | Web search |
| `/read <url>` | Read and display a URL |
| `/crawl <url>` | Crawl an entire website |
| `/browse <url>` | Interactive browser |
| `/headers <url>` | Analyze security headers |
| `/decode <data>` | Auto-detect and decode |
| `/encode <format> <data>` | Encode data |
| `/hash <data>` | Generate all hashes |
| `/cve <CVE-ID>` | Lookup CVE details |
| `/think [fast/deep/paranoid]` | Set thinking depth |
| `/learn <url-or-topic>` | Learn from URL |
| `/evolve` | Run evolution cycle |
| `/kb [search/list/stats]` | Knowledge base |
| `/model [list/set]` | LLM model |
| `/theme <name>` | Change theme |
| `/stats` | Show statistics |
| `/history` | View history |
| `/clear` | Clear terminal |
| `/help` | Show help |
| `/quit` | Exit |

### Natural Conversation

Just type your question directly:

```
PHANTOM▶ How do I exploit CVE-2024-1234?
PHANTOM▶ What does this code do? [paste code]
PHANTOM▶ Explain SQL injection prevention
PHANTOM▶ Teach me about privilege escalation
```

---

## The Five Thinking Engines

PHANTOM's core differentiator. Each engine provides unique analysis:

| Engine | Purpose | Mode |
|--------|---------|------|
| **Chain-of-Thought** | Step-by-step reasoning | Always |
| **Parallel** | Three perspectives (Red/Blue/Research) | deep+ |
| **Devil's Advocate** | Finds flaws and assumptions | deep+ |
| **Meta-Cognition** | Quality assessment | deep+ |
| **Red Team** | Stress testing scenarios | paranoid |
| **Synthesis** | Merges all into final answer | Always |

---

## LLM Backend Priority

PHANTOM auto-detects backends in this priority order:

1. **Ollama** (local, free, private) — Best if running
2. **Groq** (cloud, fast, free tier) — No local GPU needed
3. **OpenAI** (cloud, GPT-4o) — Requires API key
4. **Anthropic** (cloud, Claude) — Requires API key
5. **Google Gemini** (cloud) — Requires API key
6. **OpenRouter** (access 100+ models) — Single API key

---

## Project Structure

```
phantom/
├── phantom.py           # Main entry point
├── core/
│   ├── config.py      # Configuration manager
│   ├── llm.py        # LLM backend abstraction
│   ├── thinking.py    # Five thinking engines
│   ├── memory.py      # Conversation memory
│   ├── evolution.py   # Self-evolution engine
│   └── session.py     # Session manager
├── tools/
│   ├── web_search.py      # Multi-engine search
│   ├── web_crawler.py    # Web crawler
│   ├── web_viewer.py      # Terminal viewer
│   ├── decoder.py         # Encode/decode engine
│   └── knowledge_base.py   # Knowledge store
├── agents/
│   ├── base_agent.py      # Base agent
│   ├── web_agent.py       # Web research
│   ├── decoder_agent.py    # Decoding
│   ├── analyzer_agent.py    # Code analysis
│   ├── report_agent.py     # Reports
│   ├── educator_agent.py   # Teaching
│   └── orchestrator.py     # Task routing
└── ui/
    ├── splash.py          # Splash screens
    ├── terminal.py       # Rich UI
    ├── themes.py         # Color themes
    └── progress.py      # Progress bars
```

---

## Environment Variables

```bash
# LLM Providers
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GROQ_API_KEY="gsk_..."
export OPENROUTER_API_KEY="sk-or-..."

# Optional Services
export SHODAN_API_KEY="..."
export GITHUB_TOKEN="ghp_..."
export GOOGLE_API_KEY="..."

# Configuration
export PHANTOM_THEME="matrix"
```

---

## Themes

| Theme | Preview |
|-------|---------|
| **matrix** | Green on black (default) |
| **dracula** | Purple/pink tones |
| **monokai** | Yellow/green tones |
| **blood** | Red/black tones |

Switch with `/theme <name>`.

---

## Requirements

### Full Install

- Python 3.8+
- 4GB RAM minimum
- Network connection (for cloud LLMs)

### Minimal Install

- Python 3.8+
- 512MB RAM
- For Termux/Android devices

---

## Security Notice

PHANTOM is designed for **authorized security research, CTF competitions, and education**. Always:

- Obtain proper authorization before testing
- Follow responsible disclosure practices
- Use only on systems you own or have permission to test
- Never use for malicious purposes

---

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**PHANTOM v2.0.0-OMEGA** — *"What you can't see can still compromise you."*

</div>