#!/usr/bin/env python3
"""
HexStrike AI MCP Server - HTTP Transport Wrapper
啟用 streamable-http transport 並配置端點匹配 MCP Adapter
"""

import os
import sys

# 添加當前目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hexstrike_mcp import HexStrikeClient, setup_mcp_server, logger

def main():
    """啟動帶有 HTTP transport 的 MCP 服務器"""
    # 從環境變量獲取配置
    server_url = os.environ.get("HEXSTRIKE_SERVER_URL", "http://localhost:8888")
    mcp_host = os.environ.get("FASTMCP_HOST", "0.0.0.0")
    mcp_port = int(os.environ.get("FASTMCP_PORT", "8889"))

    # 初始化 HexStrike 客戶端
    hexstrike_client = HexStrikeClient(server_url)

    # 檢查服務器健康狀態
    health = hexstrike_client.check_health()
    if "error" not in health:
        logger.info(f"🎯 Connected to HexStrike AI API: {server_url}")
        logger.info(f"🏥 Server status: {health.get('status')}")

    # ⚠️ CRITICAL: 在初始化時傳入 streamable_http_path
    # MCP Adapter 使用 /messages/ 端點
    mcp = setup_mcp_server(
        hexstrike_client,
        streamable_http_path="/messages/",  # 匹配 MCP Adapter
        stateless_http=True                  # 無狀態模式，無需 session_id
    )

    logger.info(f"🚀 Starting HexStrike MCP Server on {mcp_host}:{mcp_port}")
    logger.info(f"📡 Transport: streamable-http (stateless)")
    logger.info(f"🔗 Endpoint: /messages/")

    # FastMCP.run() 的 host/port 在 streamable-http 模式下不需要
    # 因為已在 FastMCP.__init__() 中配置
    mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()
