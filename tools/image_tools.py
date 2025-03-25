from langchain_core.tools import tool
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from langgraph.types import interrupt
from loguru import logger


@tool
def generate_image(prompt: str) -> str:
    """Generate an image using DALL-E 3 based on the prompt."""
    dalle = DallEAPIWrapper(model="dall-e-3")
    image_url = dalle.run(prompt)
    return f"Generated image URL: {image_url}"


@tool
def get_human_feedback(image_url: str) -> str:
    """Get human feedback on whether to upload the image to IPFS."""
    response = interrupt(
        {
            "message": f"Image has been generated: {image_url}\nWould you like to upload this to IPFS? (yes/no)"
        }
    )
    logger.info(f"Human feedback received: {response['data']}")
    return response["data"]
