from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda


class CallLLM:
    """Node for calling the LLM with the current messages."""

    def __init__(self, model):
        self.model = model

    async def ainvoke(self, state, config=None):
        messages = state["messages"]
        response = await self.model.ainvoke(messages)
        return {"messages": [response]}


def create_call_llm_node(model):
    """Create a callable node for the LLM."""
    return RunnableLambda(CallLLM(model).ainvoke)
