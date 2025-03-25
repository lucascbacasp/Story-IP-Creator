from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda
import uuid


class RunTool:
    """Node for running tools based on LLM tool calls."""

    def __init__(self, tools_dict):
        self.tools = tools_dict

    async def ainvoke(self, state, config=None):
        new_messages = []
        last_message = state["messages"][-1]

        for tool_call in last_message.tool_calls:
            try:
                tool_name = tool_call["name"]
                if tool_name in self.tools:
                    tool = self.tools[tool_name]

                    # Extract just the string value for image_data if that's the parameter
                    if (
                        tool_name == "upload_image_to_ipfs"
                        and "image_data" in tool_call["args"]
                    ):
                        # Make sure we're passing just the URL string, not a complex object
                        image_url = tool_call["args"]["image_data"]
                        result = await tool.ainvoke({"image_data": image_url})
                    else:
                        result = await tool.ainvoke(tool_call["args"])

                    # Make sure result is a string
                    if not isinstance(result, str):
                        result = str(result)

                    new_messages.append(
                        ToolMessage(
                            content=result,
                            name=tool_call["name"],
                            tool_call_id=tool_call["id"],
                        )
                    )
                else:
                    new_messages.append(
                        ToolMessage(
                            content=f"Error: Tool '{tool_name}' not found",
                            name=tool_call["name"],
                            tool_call_id=tool_call["id"],
                        )
                    )

            except Exception as e:
                new_messages.append(
                    ToolMessage(
                        content=f"Error executing tool: {str(e)}",
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"],
                    )
                )

        return {"messages": new_messages}


class RunIPFSTool:
    """Node specifically for running the IPFS upload tool."""

    def __init__(self, upload_to_ipfs_tool):
        self.upload_to_ipfs_tool = upload_to_ipfs_tool

    async def ainvoke(self, state, config=None):
        new_messages = []
        last_message = state["messages"][-1]

        for tool_call in last_message.tool_calls:
            try:
                # Extract just the string value for image_data if that's the parameter
                if "image_data" in tool_call["args"]:
                    # Make sure we're passing just the URL string, not a complex object
                    image_url = tool_call["args"]["image_data"]
                    result = await self.upload_to_ipfs_tool.ainvoke(
                        {"image_data": image_url}
                    )
                else:
                    result = await self.upload_to_ipfs_tool.ainvoke(tool_call["args"])

                # Make sure result is a string
                if not isinstance(result, str):
                    result = str(result)

                new_messages.append(
                    ToolMessage(
                        content=result,
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"],
                    )
                )

            except Exception as e:
                new_messages.append(
                    ToolMessage(
                        content=f"Error executing tool: {str(e)}",
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"],
                    )
                )

        return {"messages": new_messages}


def create_run_tool_node(tools_dict):
    """Create a callable node for running tools."""
    return RunnableLambda(RunTool(tools_dict).ainvoke)


def create_run_ipfs_tool_node(upload_to_ipfs_tool):
    """Create a callable node for running the IPFS upload tool."""
    return RunnableLambda(RunIPFSTool(upload_to_ipfs_tool).ainvoke)
