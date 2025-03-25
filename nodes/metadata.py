from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
import uuid
import json
import re


class GenerateMetadata:
    """Node for generating metadata for the uploaded image."""

    def __init__(self, simple_model):
        self.simple_model = simple_model

    async def ainvoke(self, state, config=None):
        print("Generating metadata...")

        # Get the IPFS URI from the previous message
        ipfs_uri = None
        for message in reversed(state["messages"]):
            if (
                isinstance(message, ToolMessage)
                and message.name == "upload_image_to_ipfs"
            ):
                if "Successfully uploaded image to IPFS:" in message.content:
                    ipfs_uri = message.content.split(
                        "Successfully uploaded image to IPFS: "
                    )[1].strip()
                    break

        if not ipfs_uri:
            return {
                "messages": [
                    AIMessage(content="Failed to extract IPFS URI from upload result.")
                ]
            }

        # Get the original image description from earlier messages
        original_description = ""
        for message in state["messages"]:
            if isinstance(message, HumanMessage) and "Generate" in message.content:
                original_description = message.content
                break

        # Create a prompt for the LLM to generate metadata in the exact format we need
        metadata_prompt = HumanMessage(
            content=f"""I've uploaded an image to IPFS with URI: {ipfs_uri}. 
                The image was created based on this description: "{original_description}"

                Please generate metadata for this IP with the following fields:
                1. Name: A creative name for this IP
                2. Description: A detailed description of what's in the image
                3. Attributes: A list of traits in the exact format shown below:

                [
                {{"trait_type": "style", "value": "[one-word style descriptor]"}},
                {{"trait_type": "mood", "value": "[one-word mood descriptor]"}},
                {{"trait_type": "setting", "value": "[one-word setting descriptor]"}}
                ]

                Format your response exactly like this:
                {{
                "name": "Your creative name here",
                "description": "Your detailed description here",
                "attributes": [
                    {{"trait_type": "style", "value": "anime"}},
                    {{"trait_type": "mood", "value": "exciting"}},
                    {{"trait_type": "setting", "value": "mountains"}}
                ]
            }}"""
        )

        # Get LLM to generate metadata suggestions in the correct format
        metadata_response = await self.simple_model.ainvoke([metadata_prompt])

        # Store the IPFS URI in the message for the next node
        return {
            "messages": [
                AIMessage(
                    content=f"IPFS_URI: {ipfs_uri}\n\n{metadata_response.content}"
                )
            ]
        }


class CreateMetadata:
    """Node for creating metadata for the IP asset."""

    def __init__(self, create_metadata_tool):
        self.create_metadata_tool = create_metadata_tool

    async def ainvoke(self, state, config=None):
        print("Creating metadata...")
        new_messages = []

        # Get the metadata suggestions from the LLM
        metadata_message = None
        for message in reversed(state["messages"]):
            if isinstance(message, AIMessage) and "IPFS_URI:" in message.content:
                metadata_message = message
                break

        if not metadata_message:
            return {
                "messages": [AIMessage(content="Failed to find metadata suggestions.")]
            }

        # Extract IPFS URI from the message
        ipfs_uri = metadata_message.content.split("IPFS_URI:")[1].split("\n")[0].strip()

        # Extract the JSON part of the message
        metadata_content = metadata_message.content.split("IPFS_URI:")[1].split(
            "\n\n", 1
        )[1]

        try:
            # Try to parse the JSON directly from the LLM response
            # Look for JSON content between curly braces
            json_match = re.search(r"\{.*\}", metadata_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                metadata_dict = json.loads(json_str)

                name = metadata_dict.get("name", "AI Generated Artwork")
                description = metadata_dict.get(
                    "description", "An AI-generated artwork uploaded to IPFS"
                )
                attributes = metadata_dict.get("attributes", [])

                # Validate attributes format
                valid_attributes = []
                for attr in attributes:
                    if (
                        isinstance(attr, dict)
                        and "trait_type" in attr
                        and "value" in attr
                    ):
                        valid_attributes.append(attr)

                # If no valid attributes found, create some default ones
                if not valid_attributes:
                    valid_attributes = [
                        {"trait_type": "style", "value": "digital"},
                        {"trait_type": "creator", "value": "AI"},
                    ]
            else:
                # Fallback to manual parsing if JSON extraction fails
                name = "AI Generated Artwork"
                description = "An AI-generated artwork uploaded to IPFS"

                # Extract name if present
                if "name" in metadata_content.lower():
                    name_match = re.search(
                        r'"name"\s*:\s*"([^"]+)"', metadata_content, re.IGNORECASE
                    )
                    if name_match:
                        name = name_match.group(1)

                # Extract description if present
                if "description" in metadata_content.lower():
                    desc_match = re.search(
                        r'"description"\s*:\s*"([^"]+)"',
                        metadata_content,
                        re.IGNORECASE,
                    )
                    if desc_match:
                        description = desc_match.group(1)

                # Create default attributes
                valid_attributes = [
                    {"trait_type": "style", "value": "digital"},
                    {"trait_type": "creator", "value": "AI"},
                ]

            # Call the create_ip_metadata tool with properly formatted data
            result = await self.create_metadata_tool.ainvoke(
                {
                    "image_uri": ipfs_uri,
                    "name": name,
                    "description": description,
                    "attributes": valid_attributes,
                }
            )

            new_messages.append(
                ToolMessage(
                    content=result,
                    name="create_ip_metadata",
                    tool_call_id=str(uuid.uuid4()),
                )
            )

        except Exception as e:
            new_messages.append(
                ToolMessage(
                    content=f"Error creating metadata: {str(e)}",
                    name="create_ip_metadata",
                    tool_call_id=str(uuid.uuid4()),
                )
            )

        return {"messages": new_messages}


def create_generate_metadata_node(simple_model):
    """Create a callable node for generating metadata."""
    return RunnableLambda(GenerateMetadata(simple_model).ainvoke)


def create_create_metadata_node(create_metadata_tool):
    """Create a callable node for creating metadata."""
    return RunnableLambda(CreateMetadata(create_metadata_tool).ainvoke)
