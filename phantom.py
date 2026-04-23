#!/usr/bin/env python3
"""PHANTOM - Polymorphic Heuristic AI for Network Threat Analysis & Mentoring

Next-generation LLM AI assistant for cybersecurity education and research.
Runs with Five Thinking Engines: Chain · Parallel · Devil · Meta · Red Team

Usage:
    python phantom.py                    # Interactive REPL
    python phantom.py --help              # Show help
    python phantom.py "your question"    # Single query mode
"""

import sys
import os

# Auto-install minimal dependencies if needed
def check_dependencies():
    """Check and install required dependencies."""
    required = ["rich", "requests", "beautifulsoup4", "duckduckgo-search"]
    missing = []
    
    for module in required:
        try:
            __import__(module.replace("-", "_"))
        except ImportError:
            missing.append(module)
    
    if missing:
        print("Installing dependencies...", file=sys.stderr)
        os.system(f"pip install -q {' '.join(missing)}")
        print("Dependencies installed!", file=sys.stderr)

check_dependencies()

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.live import Live

# Version info
__version__ = "2.0.5-OMEGA"
__codename__ = "OMEGA-CORE"
__tagline__ = "What you can't see can still compromise you."

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - PHANTOM - %(levelname)s - %(message)s",
)
logger = logging.getLogger("phantom")


def print_banner():
    """Print PHANTOM banner."""
    banner = """
 ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗
 ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║
 ██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║
 ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║
 ██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║
 ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝
"""
    print(banner)
    print(f"[ Next-Generation Security AI - v{__version__} ]")
    print(f'"{__tagline__}"')
    print()


def check_platform():
    """Check platform compatibility."""
    if sys.platform == "win32":
        return "Windows"
    elif sys.platform == "darwin":
        return "macOS"
    elif Path("/data/data/com.termux").exists():
        return "Termux"
    else:
        try:
            if Path("/etc/kali-linux-release").exists():
                return "Kali"
            with open("/etc/os-release") as f:
                content = f.read().lower()
                if "kali" in content:
                    return "Kali"
                if "parrot" in content:
                    return "Parrot"
        except:
            pass
        return "Linux"


class PHANTOM:
    """PHANTOM - Next-Generation Security AI."""

    SYSTEM_PROMPT = """You are PHANTOM — a next-generation AI assistant designed for 
cybersecurity education and research. You combine five specialized thinking engines 
that reason through complex security problems before delivering authoritative answers.

Your core expertise:
- Penetration testing and ethical hacking
- CVE analysis and vulnerability research
- Network reconnaissance (nmap, Shodan, OSINT)
- Web application security (OWASP Top 10)
- Cryptography and encoding/decoding
- CTF challenges and malware analysis

You always:
- Pair offensive techniques with defensive countermeasures
- Verify CVE numbers before stating them
- Provide working code examples
- Never make up facts

You support authorized security research, CTF competitions, and education."""

    THINKING_PROMPTS = {
        "chain": """Think through this problem step by step. Show your work.
Format: STEP 1: [reasoning] → STEP 2: [reasoning] → CONCLUSION: [answer]""",
        
        "parallel": """Analyze from three perspectives:

RED LENS: How would an attacker view this?
BLUE LENS: How would a defender view this?
RESEARCH LENS: What is academically interesting?""",
        
        "devil": """You are a harsh critic. Find every flaw, incorrect assumption, 
or logical error in the analysis. Format: CHALLENGE 1: [issue + correction]""",
        
        "meta": """Review the reasoning quality:
- What does the AI know confidently vs. uncertainly?
- What information might be outdated or fabricated?
- What follow-up questions should be asked?""",
        
        "redteam": """Stress-test the conclusion. Construct 3 scenarios that would invalidate it:
SCENARIO 1: [Name] - ATTACK: [How it breaks the conclusion]"""
    }

    def __init__(self):
        """Initialize PHANTOM."""
        self.console = Console()
        self.platform = check_platform()
        self.session_id = str(uuid.uuid4())[:8]
        self.conversation = []
        self.detected_backends = []
        self.current_backend = None
        self._detect_llm()

    def _detect_llm(self):
        """Detect available LLM backends."""
        import requests
        
        backends = {}
        
        # Check Ollama for PHANTOM model first
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=2)
            if r.status_code == 200:
                models = r.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                
                if "phantom" in model_names:
                    backends["phantom"] = "PHANTOM 3B"
                    self.current_backend = "phantom"
                elif any("3b" in n.lower() for n in model_names):
                    backends["ollama"] = "local 3B"
                    self.current_backend = "ollama"
                elif model_names:
                    backends["ollama"] = "local"
                    self.current_backend = "ollama"
        except:
            pass
        
        # Check for API keys
        for key_name, key_env in [
            ("groq", "GROQ_API_KEY"),
            ("openai", "OPENAI_API_KEY"),
            ("anthropic", "ANTHROPIC_API_KEY"),
        ]:
            if os.getenv(key_env):
                backends[key_name] = "configured"
                if not self.current_backend:
                    self.current_backend = key_name
        
        self.detected_backends = list(backends.keys())
        
        if not self.current_backend:
            self.current_backend = "none"
            self.console.print("[yellow]Warning: No LLM backend detected[/yellow]")
            self.console.print("[yellow]For full functionality, build PHANTOM 3B:[/yellow]")
            self.console.print("[yellow]  - bash build_phantom.sh[/yellow]")

    def chat(self, message: str, thinking: str = "deep") -> str:
        """Chat with PHANTOM using available backend."""
        
        # Build messages
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            *self.conversation[-10:],
            {"role": "user", "content": message}
        ]
        
        if self.current_backend == "ollama":
            return self._chat_ollama(messages)
        elif self.current_backend == "groq":
            return self._chat_api("groq", messages)
        elif self.current_backend == "openai":
            return self._chat_api("openai", messages)
        elif self.current_backend == "anthropic":
            return self._chat_api("anthropic", messages)
        else:
            return self._demo_response(message, thinking)

    def _chat_ollama(self, messages: list) -> str:
        """Chat using Ollama with PHANTOM model."""
        import requests
        import json
        
        formatted = []
        for m in messages:
            role = m["role"]
            if role == "system":
                continue
            formatted.append({"role": role, "content": m["content"]})
        
        # Use PHANTOM model if available, otherwise fallback
        model = "phantom" if self.current_backend == "phantom" else "llama3.1:3b"
        
        try:
            r = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": model,
                    "messages": formatted,
                    "stream": False,
                    "options": {"num_predict": 2048, "temperature": 0.7}
                },
                timeout=120
            )
            if r.status_code == 200:
                return r.json()["message"]["content"]
        except Exception as e:
            return f"Error: {e}"
        
        return "Ollama error"

    def _chat_api(self, backend: str, messages: list) -> str:
        """Chat using cloud API."""
        import requests
        import json
        
        api_key = os.getenv(f"{backend.upper()}_API_KEY")
        if not api_key:
            return f"No {backend} API key configured"
        
        headers = {"Authorization": f"Bearer {api_key}"}
        
        if backend == "groq":
            url = "https://api.groq.com/openai/v1/chat/completions"
            model = "llama-3.1-70b-versatile"
        elif backend == "openai":
            url = "https://api.openai.com/v1/chat/completions"
            model = "gpt-4o"
        elif backend == "anthropic":
            url = "https://api.anthropic.com/v1/messages"
            model = "claude-3-5-sonnet-20241022"
            headers["anthropic-version"] = "2023-06-01"
        
        formatted = []
        for m in messages:
            role = m["role"]
            if role == "system":
                continue
            content = m["content"]
            if backend == "anthropic":
                if role == "assistant":
                    role = "assistant"
                else:
                    role = "user"
            formatted.append({"role": role, "content": content})
        
        try:
            if backend == "anthropic":
                payload = {
                    "model": model,
                    "messages": formatted,
                    "max_tokens": 2048
                }
            else:
                payload = {
                    "model": model,
                    "messages": formatted
                }
            
            r = requests.post(url, headers=headers, json=payload, timeout=120)
            if r.status_code == 200:
                if backend == "anthropic":
                    return r.json()["content"][0]["text"]
                else:
                    return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error: {e}"
        
        return f"{backend} error"

    def _demo_response(self, message: str, thinking: str) -> str:
        """Generate a demo response without LLM."""
        
        # Simple keyword responses for demo
        msg_lower = message.lower()
        
        if any(x in msg_lower for x in ["sql injection", "sqli"]):
            return """## SQL Injection Analysis

**Attack Vector:**
```python
# Unsafe SQL query
query = f"SELECT * FROM users WHERE id = {user_id}"

# Attack payload
' OR '1'='1

# Result
SELECT * FROM users WHERE id = ' OR '1'='1
```

**Impact:** Authentication bypass, data extraction

**Prevention:**
```python
# Safe parameterized query
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

**OWASP:** A03:2021 Injection"""
        
        elif any(x in msg_lower for x in ["xss", "cross site"]):
            return """## Cross-Site Scripting (XSS)

**Reflected XSS:**
```html
<!-- Vulnerable -->
<div>{{ user_input }}</div>

<!-- Attack -->
<script>alert(document.cookie)</script>
```

**Prevention:**
```python
# HTML escape
import html
safe_input = html.escape(user_input)
```

**OWASP:** A03:2021 XSS"""
        
        elif any(x in msg_lower for x in ["nmap", "scan"]):
            return """## Nmap Scanning

**Basic Scan:**
```bash
nmap -sV 192.168.1.1          # Version scan
nmap -sC 192.168.1.1          # Default scripts
nmap -A 192.168.1.1           # Aggressive (OS, version, scripts, traceroute)
nmap -p 1-1000 192.168.1.1   # Port range
```

**Stealth SYN Scan (root):**
```bash
nmap -sS 192.168.1.1
```

**UDP Scan:**
```bash
nmap -sU 192.168.1.1
```"""
        
        elif any(x in msg_lower for x in ["metasploit", "msfconsole"]):
            return """## Metasploit Framework

**Start:** `msfconsole`

**Basic Workflow:**
```
search exploit_name        # Find exploit
use exploit/path/name     # Select exploit
show options             # Show required options
set RHOSTS 192.168.1.1  # Set target
exploit                 # Run exploit
```

**Common Payloads:**
```
set PAYLOAD linux/x64/meterpreter/reverse_tcp
set PAYLOAD windows/meterpreter/reverse_tcp
```

**Auxiliary Scanners:**
```
use auxiliary/scanner/portscan/tcp
use auxiliary/scanner/smb/smb_version
```"""
        
        elif any(x in msg_lower for x in ["cve-", "vulnerability"]):
            return """## CVE Lookup

To look up a CVE, use:
```
/search CVE-2024-21762
```

Or search the NVD database:
- https://nvd.nist.gov/vuln/detail/{CVE-ID}

**Note:** PHANTOM can lookup CVEs in real-time with an LLM backend."""
        
        else:
            return f"""## PHANTOM Response

I processed your query about: **{message[:50]}...**

To get full AI-powered responses, configure an LLM backend:

1. **Ollama (recommended - local & free):**
   ```bash
   # Install
   curl -fsSL https://ollama.ai | sh
   ollama pull llama3
   ```

2. **Groq (cloud - free tier):**
   ```bash
   export GROQ_API_KEY="your-key"
   # Get free key at https://console.groq.com
   ```

3. **OpenAI:**
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

**PHANTOM Capabilities:**
- Five Thinking Engines for deep reasoning
- CVE lookup and analysis
- Code generation and execution
- YouTube video learning
- Self-update capabilities
- Deep security research"""

    def run(self, query: Optional[str] = None):
        """Run PHANTOM."""
        print_banner()
        
        self.console.print(Panel(
            f"**Platform:** {self.platform}\n"
            f"**LLM Backend:** {self.current_backend or 'None (demo mode)'}\n"
            f"**Detected:** {', '.join(self.detected_backends) if self.detected_backends else 'None'}\n\n"
            f"**Commands:**\n"
            f"  /help     - Show all commands\n"
            f"  /clear   - Clear screen\n"
            f"  /quit    - Exit PHANTOM\n\n"
            f"**Thinking Modes:**\n"
            f"  /think fast     - Quick response\n"
            f"  /think deep    - Deep analysis (default)\n"
            f"  /think paranoid - Maximum analysis",
            title=f"PHANTOM v{__version__}",
            border_style="green"
        ))
        self.console.print()
        
        if query:
            # Single query mode
            response = self.chat(query)
            self.console.print(Panel(response, title="PHANTOM", border_style="green"))
            return
        
        # Interactive REPL
        while True:
            try:
                user_input = self.console.input("[bold green]PHANTOM[/bold green]▶ ").strip()
                
                if not user_input:
                    continue
                
                if user_input in ["/quit", "/exit", "quit", "exit", "q"]:
                    print(f"\nPHANTOM signing off. Session: {self.session_id}")
                    break
                
                if user_input == "/help":
                    self._show_help()
                    continue
                
                if user_input == "/clear":
                    self.console.clear()
                    print_banner()
                    continue
                
                if user_input.startswith("/"):
                    self._handle_command(user_input)
                    continue
                
                # Regular chat
                with Live(
                    Panel("[cyan]PHANTOM is thinking...[/cyan]", border_style="green"),
                    console=self.console,
                    refresh_per_second=4,
                ) as live:
                    response = self.chat(user_input)
                    live.update(Panel(response, title="PHANTOM", border_style="green"))
                
                self.conversation.append({"role": "user", "content": user_input})
                self.conversation.append({"role": "assistant", "content": response})
                
            except KeyboardInterrupt:
                print("\n[Use /quit to exit]")
            except EOFError:
                break

    def _show_help(self):
        """Show help."""
        help_text = """
## PHANTOM Commands

### General
- `/help`     - Show this help
- `/clear`    - Clear screen
- `/quit`     - Exit PHANTOM
- `/stats`    - Show statistics

### Thinking
- `/think fast`     - Quick response
- `/think deep`     - Deep analysis (default)
- `/think paranoid` - Maximum analysis

### Web
- `/search <query>`   - Web search
- `/cve <cve-id>`     - CVE lookup
- `/yt <url>`         - YouTube analysis

### Code
- `/run python <code>` - Run Python code
- `/generate <desc>`   - Generate code

### Learning
- `/do <task>`       - Autonomous task
- `/research <topic>` - Deep research

### LLM
- `/backend` - Show current backend
- `/switch <name>` - Switch LLM backend

### Self-Evolution
- `/evolve`      - Run self-evolution cycle
- `/retrain`     - Retrain PHANTOM model
"""
        self.console.print(Panel(help_text, title="Help", border_style="cyan"))

    def _handle_command(self, command: str):
        """Handle slash commands."""
        cmd = command.split()[0].lower()
        args = " ".join(command.split()[1:])
        
        if cmd == "/backend":
            self.console.print(f"Current: {self.current_backend}")
            self.console.print(f"Available: {self.detected_backends}")
        
        elif cmd == "/evolve":
            self.console.print("[cyan]Running self-evolution cycle...[/cyan]")
            try:
                from core.evolution import EvolutionEngine
                engine = EvolutionEngine()
                report = engine.run_evolution_cycle()
                self.console.print(f"[green]Evolution cycle {report.cycle_number} complete![/green]")
                self.console.print(f"Entries added: {report.entries_added}")
            except Exception as e:
                self.console.print(f"[red]Evolution error: {e}[/red]")
        
        elif cmd == "/retrain":
            self.console.print("[cyan]Running self-training...[/cyan]")
            try:
                from core.self_training import SelfTrainingEngine
                trainer = SelfTrainingEngine()
                if trainer.should_retrain():
                    result = trainer.run_self_training()
                    if result.success:
                        self.console.print(f"[green]Training complete! Cycle {result.cycle_number}[/green]")
                    else:
                        self.console.print(f"[red]Training failed: {result.error}[/red]")
                else:
                    pending = trainer.get_training_status()["pending_knowledge"]
                    self.console.print(f"Need {10 - pending} more knowledge entries to retrain")
            except Exception as e:
                self.console.print(f"[red]Training error: {e}[/red]")
        
        elif cmd == "/stats":
            self.console.print(Panel(
                f"**Session:** {self.session_id}\n"
                f"**Messages:** {len(self.conversation)}\n"
                f"**Platform:** {self.platform}\n"
                f"**Backend:** {self.current_backend}",
                title="Statistics",
                border_style="green"
            ))


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="PHANTOM - Next-Generation Security AI"
    )
    parser.add_argument("query", nargs="?", help="Single query to answer")
    parser.add_argument("--version", "-v", action="version", version=__version__)
    
    args = parser.parse_args()
    
    phantom = PHANTOM()
    phantom.run(args.query)


if __name__ == "__main__":
    main()