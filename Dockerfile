# HexStrike-ai Dockerfile - 基於社區版本
# 僅添加 HTTP transport 支持和必要的安全工具

FROM python:3.11-slim-bookworm

LABEL maintainer="ARXON Project"
LABEL description="HexStrike-ai MCP Security Tools Server"
LABEL version="2.0.0"

ENV DEBIAN_FRONTEND=noninteractive

# ========================================
# Layer 1: 系統依賴 + P0 核心工具
# ========================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 基礎工具
    curl wget git gnupg ca-certificates \
    # 網絡基礎
    iputils-ping net-tools dnsutils \
    # P0 核心 - 網絡掃描
    nmap masscan \
    # US-002: Network 工具擴展 (network_tools 類別)
    arp-scan nbtscan \
    # 額外網絡工具 (非 network_tools 類別但實用)
    tcpdump traceroute netcat-openbsd \
    # P0 核心 - Web 安全
    sqlmap dirb \
    # P0 核心 - 密碼破解
    hydra john \
    # P0 核心 - 二進制分析
    binwalk \
    # P1 - 二進制/調試/逆向 (radare2 installed separately below)
    gdb \
    # P1 - 密碼破解 (hashcat opencl 可選)
    hashcat \
    # P1 - SMB / enum (enum4linux-ng installed via pip below)
    smbmap \
    # radare2 build deps
    build-essential pkg-config \
    # US-004: Forensics 工具
    sleuthkit \
    # US-004: Password 工具
    ophcrack \
    # US-004: Vuln Scanning 工具
    lynis \
    # P1 - 額外工具
    smbclient \
    # nikto Perl 依賴
    libjson-perl libxml-writer-perl \
    # 健康檢查
    jq \
    # enum4linux-ng full deps (nmblookup, net)
    samba-common-bin \
    && rm -rf /var/lib/apt/lists/*

# ========================================
# Layer 2: 從源碼安裝 nikto (直接複製， not符號鏈接)
# ========================================
RUN git clone --depth 1 https://github.com/sullo/nikto.git /opt/nikto \
    && cp /opt/nikto/program/nikto.pl /usr/local/bin/nikto \
    && cp /opt/nikto/program/nikto.conf.default /etc/nikto.conf \
    && echo "EXECDIR=/opt/nikto/program" >> /etc/nikto.conf \
    && chmod +x /usr/local/bin/nikto

# ========================================
# Layer 3: radare2 (P1 - from official installer script)
# Debian bookworm main does not package radare2, install from upstream release.
# ========================================
RUN git clone --depth 1 --branch 5.9.0 https://github.com/radareorg/radare2.git /opt/radare2 \
    && /opt/radare2/sys/install.sh

# ========================================
# Layer 4: Go 工具 (P0 核心)
# ========================================
RUN curl -sL https://go.dev/dl/go1.22.0.linux-amd64.tar.gz | tar -C /usr/local -xz \
    && export PATH=$PATH:/usr/local/go/bin:/root/go/bin \
    && go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest \
    && go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest \
    && go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest \
    && go install -v github.com/OJ/gobuster/v3@latest \
    && go install -v github.com/ffuf/ffuf/v2@latest \
    && go install -v github.com/owasp-amass/amass/v4/...@latest \
    && go install -v github.com/projectdiscovery/katana/cmd/katana@latest \
    && go install -v github.com/hahwul/dalfox/v2@latest \
    && go install -v github.com/hakluke/hakrawler@latest \
    && mv /root/go/bin/* /usr/local/bin/ \
    && rm -rf /root/go /usr/local/go

# ========================================
# Layer 5: Rust 工具 (feroxbuster)
# ========================================
RUN curl -sL https://github.com/epi052/feroxbuster/releases/latest/download/x86_64-linux-feroxbuster.tar.gz \
    | tar -xz -C /usr/local/bin/ \
    && chmod +x /usr/local/bin/feroxbuster

# ========================================
# Layer 6: Python 應用
# ========================================
WORKDIR /app

# 複製依賴文件
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir requests flask mcp

# US-003: Web Security 工具擴展 (單獨層避免依賴衝突)
RUN pip install --no-cache-dir wfuzz wafw00f dirsearch

# ========================================
# Layer 7: Python 安全工具擴展 (P1: autorecon, enum4linux-ng)
# Both are installed directly from GitHub:
#   - enum4linux-ng is not published on PyPI; upstream at cddmp/enum4linux-ng
#   - autorecon on PyPI requires Python >=3.12; we use Tib3rius/AutoRecon
#     main branch which still supports 3.11.
# ========================================
RUN pip install --no-cache-dir \
    git+https://github.com/cddmp/enum4linux-ng.git \
    git+https://github.com/Tib3rius/AutoRecon.git

# ========================================
# Layer 8: Web security Python tools (P1)
# Skipped tools (not installable via pip):
#   - xsser, dotdotpwn, paramspider: not on PyPI (require git source install)
#   - wpscan: requires Ruby runtime (~200MB), too heavy for this image
# ========================================
RUN pip install --no-cache-dir arjun \
    && pip install --no-cache-dir uro

# 複製應用代碼
# ⚠️ 文件角色說明 (避免混淆):
# - hexstrike_server.py: Flask HTTP API 服務器 (端口 8888)
# - hexstrike_mcp.py: FastMCP 工具包裝器 + setup_mcp_server() 函數
# - run_http.py: HTTP transport 啟動腳本 (端口 8889)
COPY hexstrike_server.py .
COPY hexstrike_mcp.py .
COPY run_http.py .

# 創建日誌目錄
RUN mkdir -p /var/log/hexstrike

# 環境變量
ENV HEXSTRIKE_SERVER_URL=http://localhost:8888 \
    FASTMCP_HOST=0.0.0.0 \
    FASTMCP_PORT=8889 \
    LOG_LEVEL=info \
    PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8888 8889

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -sf http://localhost:8888/health || exit 1

# 啟動命令 - 使用 entrypoint 腳本
COPY docker-entrypoint-v2.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
CMD ["/docker-entrypoint.sh"]
