#!/bin/bash
# docker-entrypoint-v2.sh - 啟動 HTTP API 和 MCP 服務器

set -e

echo "🔥 HexStrike AI v2.0 - Starting..."

# 啟動 HTTP API 服務器 (後台)
echo "📡 Starting HTTP API Server on :8888"
python3 hexstrike_server.py --port 8888 &

# 等待 HTTP API 就緒
sleep 5

# 啟動 MCP 服務器 (前台) - 使用 streamable_http transport
echo "🚀 Starting MCP Server on :8889 (streamable_http transport)"
exec python3 run_http.py
