#!/usr/bin/env bash
#===============================================================================
# PHANTOM Installer - Smart cross-platform installer
# Supports: Linux · macOS · Windows · Termux/Android · Kali · Parrot · BlackArch
#===============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

BOLD='\033[1m'
DIM='\033[2m'

print_color() {
    echo -e "${1}${2}${NC}"
}

detect_os() {
    if [ -f "/data/data/com.termux/files/usr/etc/os-release" ] || [ -d "/data/data/com.termux" ]; then
        echo "termux"
    elif [ -f "/etc/kali-linux-release" ]; then
        echo "kali"
    elif [ -f "/etc/debian_version" ]; then
        if grep -qi "parrot" /etc/os-release 2>/dev/null; then
            echo "parrot"
        else
            echo "debian"
        fi
    elif [ -f "/etc/arch-release" ]; then
        echo "arch"
    elif [ "$(uname)" = "Darwin" ]; then
        echo "macos"
    elif [ "$(uname)" = "MINGW"* ] || [ "$(uname)" = "CYGWIN"* ]; then
        echo "windows"
    else
        echo "linux"
    fi
}

check_python() {
    if command -v python3 &>/dev/null; then
        PYTHON=$(command -v python3)
    elif command -v python &>/dev/null; then
        PYTHON=$(command -v python)
    else
        echo "Error: Python not found"
        exit 1
    fi

    VERSION=$($PYTHON --version 2>&1 | cut -d' ' -f2)
    print_color "$CYAN" "Found Python $VERSION"

    MAJOR=$(echo $VERSION | cut -d. -f1)
    MINOR=$(echo $VERSION | cut -d. -f2)

    if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 8 ]; then
        return 0
    else
        print_color "$YELLOW" "Warning: Python 3.8+ recommended"
    fi
}

check_pip() {
    if $PYTHON -m pip --version &>/dev/null; then
        return 0
    elif $PYTHON -m ensurepip &>/dev/null; then
        $PYTHON -m ensurepip --upgrade 2>/dev/null || true
        return 0
    else
        print_color "$YELLOW" "Warning: pip not found, may need manual install"
        return 1
    fi
}

install_termux() {
    print_color "$CYAN" "Detected Termux environment"

    print_color "$CYAN" "Updating package lists..."
    pkg update -y 2>/dev/null || true

    print_color "$CYAN" "Installing required packages..."
    pkg install -y python 2>/dev/null || true
    pkg install -y libxml2 libxslt 2>/dev/null || true

    print_color "$CYAN" "Upgrading pip..."
    pip install --upgrade pip 2>/dev/null || true
}

install_debian() {
    print_color "$CYAN" "Detected Debian-based system"

    print_color "$CYAN" "Updating package lists..."
    sudo apt update -y 2>/dev/null || apt update -y 2>/dev/null || true

    print_color "$CYAN" "Installing required packages..."
    sudo apt install -y python3 python3-pip python3-venv git 2>/dev/null || \
    apt install -y python3 python3-pip python3-venv git 2>/dev/null || true
}

install_arch() {
    print_color "$CYAN" "Detected Arch-based system"

    print_color "$CYAN" "Installing required packages..."
    sudo pacman -Sy --noconfirm python python-pip git 2>/dev/null || \
    pacman -Sy --noconfirm python python-pip git 2>/dev/null || true
}

install_macos() {
    print_color "$CYAN" "Detected macOS"

    if ! command -v brew &>/dev/null; then
        print_color "$YELLOW" "Homebrew not found. Install from https://brew.sh"
    else
        print_color "$CYAN" "Using Homebrew..."
        brew install python git 2>/dev/null || true
    fi
}

create_venv() {
    print_color "$CYAN" "Creating virtual environment..."

    if [ -d "venv" ]; then
        print_color "$YELLOW" "Virtual environment already exists"
        read -p "Recreate? (y/N): " REPLY
        if [ "$REPLY" = "y" ] || [ "$REPLY" = "Y" ]; then
            rm -rf venv
            $PYTHON -m venv venv
        fi
    else
        $PYTHON -m venv venv
    fi

    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        print_color "$GREEN" "Virtual environment created and activated"
    fi
}

install_requirements() {
    print_color "$CYAN" "Installing dependencies..."

    if [ -f "requirements-minimal.txt" ]; then
        pip install -r requirements-minimal.txt
    fi

    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        print_color "$YELLOW" "requirements.txt not found, installing basic packages..."
        pip install rich requests beautifulsoup4 duckduckgo-search
    fi

    print_color "$GREEN" "Dependencies installed"
}

create_config_dir() {
    print_color "$CYAN" "Creating PHANTOM config directory..."

    CONFIG_DIR="$HOME/.phantom"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$CONFIG_DIR/data"
    mkdir -p "$CONFIG_DIR/data/knowledge"
    mkdir -p "$CONFIG_DIR/data/sessions"
    mkdir -p "$CONFIG_DIR/data/evolution"
    mkdir -p "$CONFIG_DIR/data/cache"
    mkdir -p "$CONFIG_DIR/logs"

    print_color "$GREEN" "Config directory: $CONFIG_DIR"
}

add_alias() {
    print_color "$CYAN" "Adding alias to shell configuration..."

    ALIAS_LINE="alias phantom='cd $PWD && source venv/bin/activate && python phantom.py'"

    for RC_FILE in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.bash_profile"; do
        if [ -f "$RC_FILE" ]; then
            if ! grep -q "alias phantom=" "$RC_FILE" 2>/dev/null; then
                echo "" >> "$RC_FILE"
                echo "# PHANTOM AI" >> "$RC_FILE"
                echo "$ALIAS_LINE" >> "$RC_FILE"
                print_color "$GREEN" "Added alias to $RC_FILE"
            fi
        fi
    done
}

print_banner() {
    clear
    cat << 'BANNER'
 ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗
 ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║
 ██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║
 ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║
 ██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║
 ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝
    BANNER
    echo ""
    print_color "$GREEN" "PHANTOM v2.0.0-OMEGA Installer"
    print_color "$DIM" "Polymorphic Heuristic AI for Network Threat Analysis & Mentoring"
    echo ""
}

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -m, --minimal  Install minimal dependencies (Termux/low-end devices)"
    echo "  -n, --no-venv Skip virtual environment creation"
    echo "  -u, --update   Update existing installation"
    echo "  -v, --verbose Verbose output"
    echo ""
}

main() {
    OS=$(detect_os)
    MINIMAL=false
    NO_VENV=false
    VERBOSE=false

    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                print_usage
                exit 0
                ;;
            -m|--minimal)
                MINIMAL=true
                shift
                ;;
            -n|--no-venv)
                NO_VENV=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    print_banner

    print_color "$CYAN" "Detected OS: $OS"
    echo ""

    check_python

    print_color "$CYAN" "Starting installation..."

    case "$OS" in
        termux)
            install_termux
            ;;
        debian|kali|parrot)
            install_debian
            ;;
        arch)
            install_arch
            ;;
        macos)
            install_macos
            ;;
        *)
            print_color "$YELLOW" "Generic Linux - attempting default install..."
            ;;
    esac

    if [ "$MINIMAL" = true ]; then
        print_color "$YELLOW" "Minimal mode: using requirements-minimal.txt"
        pip install -r requirements-minimal.txt
    elif [ "$NO_VENV" = false ]; then
        create_venv
        install_requirements
    else
        check_pip || true
        install_requirements
    fi

    create_config_dir
    add_alias

    echo ""
    print_color "$GREEN" "═══════════════════════════════════════════════════════════════"
    print_color "$GREEN" "  Installation complete!"
    print_color "$GREEN" "═══════════════════════════════════════════════════════════════"
    echo ""
    print_color "$CYAN" "Next steps:"
    echo "  1. Activate virtual environment: source venv/bin/activate"
    echo "  2. Run PHANTOM: python phantom.py"
    echo "  3. Or use alias: phantom"
    echo ""
    print_color "$DIM" "First run will show setup wizard. Enjoy!"
    echo ""
}

main "$@"