from langchain_mcp_adapters.client import MultiServerMCPClient


async def get_ipfs_tools():
    """Get IPFS tools from the MCP server."""
    async with MultiServerMCPClient() as client:
        await client.connect_to_server(
            "story_server",
            command="python",
            args=["../story-mcp-hub/story-sdk-mcp/server.py"],
        )
        ipfs_tools = [
            tool
            for tool in client.get_tools()
            if tool.name
            in [
                "upload_image_to_ipfs",
                "create_ip_metadata",
                "mint_and_register_ip_with_terms",
                "mint_license_tokens",
            ]
        ]
        return ipfs_tools


def get_specific_tools(ipfs_tools):
    """Extract specific tools by name from the list of IPFS tools."""
    try:
        upload_to_ipfs_tool = next(
            tool for tool in ipfs_tools if tool.name == "upload_image_to_ipfs"
        )
        create_metadata_tool = next(
            tool for tool in ipfs_tools if tool.name == "create_ip_metadata"
        )
        mint_register_ip_tool = next(
            tool
            for tool in ipfs_tools
            if tool.name == "mint_and_register_ip_with_terms"
        )
        mint_license_tokens_tool = next(
            tool for tool in ipfs_tools if tool.name == "mint_license_tokens"
        )

        return {
            "upload_to_ipfs_tool": upload_to_ipfs_tool,
            "create_metadata_tool": create_metadata_tool,
            "mint_register_ip_tool": mint_register_ip_tool,
            "mint_license_tokens_tool": mint_license_tokens_tool,
        }
    except StopIteration:
        print("Error: Could not find required tools. Available tools:")
        for tool in ipfs_tools:
            print(f"- {tool.name}")
        raise ValueError(
            "Missing required tools. Make sure all required tools are available."
        )
