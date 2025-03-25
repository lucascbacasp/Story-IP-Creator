from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableLambda
from langgraph.types import interrupt
import json


class NegotiateTerms:
    """Node for negotiating IP licensing terms with the user."""

    def __init__(self, simple_model):
        self.simple_model = simple_model

    async def ainvoke(self, state, config=None):
        # Check if this is the first negotiation or a subsequent one
        is_first_negotiation = True
        for message in state["messages"]:
            if (
                isinstance(message, AIMessage)
                and "Terms have been set for this IP:" in message.content
            ):
                is_first_negotiation = False
                break

        if is_first_negotiation:
            print("Negotiating terms...")
        else:
            print("Deliberating...")

        # Get the registration metadata from the previous message
        registration_metadata = None
        for message in reversed(state["messages"]):
            if (
                isinstance(message, ToolMessage)
                and message.name == "create_ip_metadata"
            ):
                if "Registration metadata for minting:" in message.content:
                    metadata_section = message.content.split(
                        "Registration metadata for minting:"
                    )[1].strip()

                    try:
                        registration_metadata = json.loads(metadata_section)
                        break
                    except json.JSONDecodeError:
                        pass

        if not registration_metadata:
            return {
                "messages": [
                    AIMessage(
                        content="Failed to extract registration metadata from previous steps."
                    )
                ]
            }

        # Get the original image description for context
        original_description = ""
        for message in state["messages"]:
            if isinstance(message, HumanMessage) and "Generate" in message.content:
                original_description = message.content
                break

        # Create a prompt for negotiation
        negotiation_prompt = """
            You are a helpful IP licensing assistant. You need to negotiate fair terms for this digital artwork.

            For commercial revenue share:
            - Range is 0-100%
            - 0% means the creator gets no revenue from commercial use
            - 100% means the creator gets all revenue from commercial use
            - Typical range is 5-20% for most digital art
            - Higher quality, unique art can command 15-30%
            - Consider the uniqueness and quality of the artwork

            For derivatives allowed:
            - This is a yes/no decision
            - If yes, others can create derivative works
            - If no, the artwork cannot be modified
            - Most digital art allows derivatives with proper attribution
            - Consider if the artwork has unique elements worth protecting

            Your goal is to help the user understand these terms and reach a fair agreement.
            Start by explaining these options and suggesting reasonable defaults based on the artwork.
            DO NOT use markdown formatting in your response.
            Keep your explanation concise and user-friendly.
        """

        # First message to explain terms and suggest defaults
        initial_message = HumanMessage(
            content=f"""
                The following artwork has been created and uploaded to IPFS:
                Description: {original_description}

                We need to set terms for this IP before minting:

                1. Commercial Revenue Share: What percentage of revenue should the creator receive when this IP is used commercially?
                2. Derivatives Allowed: Should others be allowed to create derivative works based on this IP?

                Please explain these options to the user and suggest reasonable defaults.
            """
        )

        # Get initial explanation from the LLM
        explanation = await self.simple_model.ainvoke(
            [SystemMessage(content=negotiation_prompt), initial_message]
        )

        # Ask the user for their preferences
        human_review = interrupt(
            {
                "question": "Please set the terms for your IP",
                "explanation": explanation.content,
                "fields": [
                    {
                        "name": "commercial_rev_share",
                        "type": "slider",
                        "min": 0,
                        "max": 100,
                        "default": 15,
                        "label": "Commercial Revenue Share (%)",
                    },
                    {
                        "name": "derivatives_allowed",
                        "type": "boolean",
                        "default": True,
                        "label": "Allow Derivative Works",
                    },
                ],
            }
        )

        # Get the user's choices
        commercial_rev_share = human_review.get("commercial_rev_share", 15)
        derivatives_allowed = human_review.get("derivatives_allowed", True)

        # Validate the commercial_rev_share is within bounds
        if (
            not isinstance(commercial_rev_share, (int, float))
            or commercial_rev_share < 0
            or commercial_rev_share > 100
        ):
            commercial_rev_share = 15  # Default to 15% if invalid

        # Prepare a message for the LLM to evaluate the user's choices
        evaluation_message = HumanMessage(
            content=f"""
                The user has selected the following terms for their digital artwork:
                - Commercial Revenue Share: {commercial_rev_share}%
                - Derivatives Allowed: {"Yes" if derivatives_allowed else "No"}

                Original artwork description: {original_description}

                Are these terms reasonable? If not, please provide specific feedback on why they might not be optimal 
                and what you would recommend instead. Be honest but tactful.

                For commercial revenue share:
                - If it's very low (0-5%), suggest they might be undervaluing their work
                - If it's very high (>50%), explain that this might discourage commercial use
                - If it's extremely high (>80%), strongly advise that this could prevent any commercial adoption

                For derivatives:
                - If they've disallowed derivatives, explain the potential benefits of allowing them
                - If they've allowed derivatives but the artwork is highly unique, mention they might want to consider restrictions

                Only suggest changes if the terms are significantly outside reasonable ranges.
                DO NOT use markdown formatting in your response.
            """
        )

        # Get evaluation from the LLM
        evaluation = await self.simple_model.ainvoke(
            [SystemMessage(content=negotiation_prompt), evaluation_message]
        )

        # Check if the LLM suggests changes - only if terms are outside reasonable ranges
        suggests_changes = False

        # For commercial revenue share, only suggest changes if outside 5-30% range
        if commercial_rev_share < 5 or commercial_rev_share > 50:
            suggests_changes = True

        # If the terms are reasonable, skip the feedback step
        if not suggests_changes:
            # Store the negotiated terms and registration metadata for the next node
            return {
                "messages": [
                    AIMessage(
                        content=f"""
                        Terms have been set for this IP:
                        - Commercial Revenue Share: {commercial_rev_share}%
                        - Derivatives Allowed: {"Yes" if derivatives_allowed else "No"}

                        Registration metadata is ready for minting.
                    """,
                        additional_kwargs={
                            "terms_data": {
                                "commercial_rev_share": commercial_rev_share,
                                "derivatives_allowed": derivatives_allowed,
                                "registration_metadata": registration_metadata,
                            }
                        },
                    )
                ]
            }

        # Only ask for feedback if the terms are outside reasonable ranges
        feedback_review = interrupt(
            {
                "question": "The AI has some feedback on your chosen terms",
                "explanation": evaluation.content,
                "fields": [
                    {
                        "name": "adjust_terms",
                        "type": "boolean",
                        "default": True,
                        "label": "Would you like to adjust your terms?",
                    }
                ],
            }
        )

        if feedback_review.get("adjust_terms", True):
            # Ask for new terms
            print("Deliberating...")
            new_terms_review = interrupt(
                {
                    "question": "Please adjust your terms",
                    "explanation": "Based on the feedback, you can modify your terms below:",
                    "fields": [
                        {
                            "name": "commercial_rev_share",
                            "type": "slider",
                            "min": 0,
                            "max": 100,
                            "default": commercial_rev_share,
                            "label": "Commercial Revenue Share (%)",
                        },
                        {
                            "name": "derivatives_allowed",
                            "type": "boolean",
                            "default": derivatives_allowed,
                            "label": "Allow Derivative Works",
                        },
                    ],
                }
            )

            # Update with new terms
            commercial_rev_share = new_terms_review.get(
                "commercial_rev_share", commercial_rev_share
            )
            derivatives_allowed = new_terms_review.get(
                "derivatives_allowed", derivatives_allowed
            )

            # Validate again
            if (
                not isinstance(commercial_rev_share, (int, float))
                or commercial_rev_share < 0
                or commercial_rev_share > 100
            ):
                commercial_rev_share = 15  # Default to 15% if invalid

        # Store the negotiated terms and registration metadata for the next node
        return {
            "messages": [
                AIMessage(
                    content=f"""
                        Terms have been set for this IP:
                        - Commercial Revenue Share: {commercial_rev_share}%
                        - Derivatives Allowed: {"Yes" if derivatives_allowed else "No"}

                        Registration metadata is ready for minting.
                """,
                    additional_kwargs={
                        "terms_data": {
                            "commercial_rev_share": commercial_rev_share,
                            "derivatives_allowed": derivatives_allowed,
                            "registration_metadata": registration_metadata,
                        }
                    },
                )
            ]
        }


def create_negotiate_terms_node(simple_model):
    """Create a callable node for negotiating terms."""
    return RunnableLambda(NegotiateTerms(simple_model).ainvoke)
