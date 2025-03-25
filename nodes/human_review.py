from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableLambda
from langgraph.types import interrupt
import uuid


def human_review_node(state):
    """Node for getting human feedback on the generated image."""
    last_message = state["messages"][-1]

    # Get image URL from the tool message
    image_url = last_message.content.split("Generated image URL: ")[1]

    human_review = interrupt(
        {"question": "Is this image what you wanted?", "image_url": image_url}
    )

    if human_review.get("action") == "continue":
        # If yes, create a tool call to upload to IPFS
        return {
            "messages": [
                AIMessage(
                    content="Uploading approved image to IPFS",
                    tool_calls=[
                        {
                            "id": str(uuid.uuid4()),
                            "name": "upload_image_to_ipfs",
                            "args": {"image_data": image_url},
                        }
                    ],
                )
            ],
            "next": "run_ipfs_tool",
        }
    else:
        # If no, send feedback to LLM to regenerate
        return {
            "messages": [
                HumanMessage(
                    content=f"I don't like that image. {human_review.get('data', 'Please generate a different image.')}"
                )
            ],
            "next": "call_llm",
        }


def handle_failed_generation(state):
    """Node for handling failed image generation."""
    # Get the original prompt from the human message
    original_prompt = ""
    for message in state["messages"]:
        if isinstance(message, HumanMessage) and "Generate" in message.content:
            original_prompt = message.content.replace("Generate ", "")
            break

    print(f"\nUnable to generate image of {original_prompt}")
    new_prompt = input("Please try a different prompt: ")

    return {
        "messages": [HumanMessage(content=f"Generate {new_prompt}")],
        "next": "call_llm",  # Go back to the LLM with the new prompt
    }


def create_human_review_node():
    """Create a callable node for human review."""
    return RunnableLambda(human_review_node)


def create_failed_generation_handler():
    """Create a callable node for handling failed generation."""
    return RunnableLambda(handle_failed_generation)
