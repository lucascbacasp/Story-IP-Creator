from typing import Annotated
from typing import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import MessagesState


# Define our state
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], "The messages in the conversation"]
    sender: str
    thread_id: str


class State(MessagesState):
    """Simple state for the agent workflow."""
