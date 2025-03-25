from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage

from models.state import State
from tools.image_tools import generate_image
from nodes.call_llm import create_call_llm_node
from nodes.run_tool import create_run_tool_node, create_run_ipfs_tool_node
from nodes.human_review import (
    create_human_review_node,
    create_failed_generation_handler,
)
from nodes.metadata import create_generate_metadata_node, create_create_metadata_node
from nodes.negotiation import create_negotiate_terms_node
from nodes.minting import create_mint_register_ip_node, create_mint_license_tokens_node


def create_workflow_graph(ipfs_tools_dict, memory=None):
    """Create the workflow graph for the agent."""

    # Extract specific tools
    upload_to_ipfs_tool = ipfs_tools_dict["upload_to_ipfs_tool"]
    create_metadata_tool = ipfs_tools_dict["create_metadata_tool"]
    mint_register_ip_tool = ipfs_tools_dict["mint_register_ip_tool"]
    mint_license_tokens_tool = ipfs_tools_dict["mint_license_tokens_tool"]

    # Initialize models
    model = ChatOpenAI(model="gpt-4o").bind_tools(
        [
            generate_image,
            upload_to_ipfs_tool,
            create_metadata_tool,
            mint_register_ip_tool,
            mint_license_tokens_tool,
        ]
    )

    # Simpler model for negotiation and other tasks
    simple_model = ChatOpenAI(model="gpt-4o-mini")

    # Create the workflow graph
    workflow = StateGraph(State)

    # Create nodes
    call_llm = create_call_llm_node(model)
    run_tool = create_run_tool_node({"generate_image": generate_image})
    run_ipfs_tool = create_run_ipfs_tool_node(upload_to_ipfs_tool)
    human_review_node = create_human_review_node()
    handle_failed_generation = create_failed_generation_handler()
    generate_metadata = create_generate_metadata_node(simple_model)
    create_metadata = create_create_metadata_node(create_metadata_tool)
    negotiate_terms = create_negotiate_terms_node(simple_model)
    mint_register_ip = create_mint_register_ip_node(mint_register_ip_tool)
    mint_license_tokens = create_mint_license_tokens_node(mint_license_tokens_tool)

    # Add nodes to the graph
    workflow.add_node("call_llm", call_llm)
    workflow.add_node("run_tool", run_tool)
    workflow.add_node("run_ipfs_tool", run_ipfs_tool)
    workflow.add_node("human_review_node", human_review_node)
    workflow.add_node("handle_failed_generation", handle_failed_generation)
    workflow.add_node("generate_metadata", generate_metadata)
    workflow.add_node("create_metadata", create_metadata)
    workflow.add_node("negotiate_terms", negotiate_terms)
    workflow.add_node("mint_register_ip", mint_register_ip)
    workflow.add_node("mint_license_tokens", mint_license_tokens)

    # Define edges
    # Start -> call LLM to generate image
    workflow.add_edge(START, "call_llm")

    # LLM -> run tool (for image generation)
    workflow.add_edge("call_llm", "run_tool")

    # Run tool -> human review (only for image generation)
    workflow.add_conditional_edges(
        "run_tool",
        lambda x: "human_review_node"
        if (
            x["messages"]
            and isinstance(x["messages"][-1], ToolMessage)
            and x["messages"][-1].name == "generate_image"
            and "Generated image URL:" in x["messages"][-1].content
        )
        else "handle_failed_generation",  # New node to handle failed generation
    )

    # Human review -> either run IPFS tool or call LLM again based on response
    workflow.add_conditional_edges(
        "human_review_node",
        lambda x: x.get("next"),  # This will be either "run_ipfs_tool" or "call_llm"
    )

    # IPFS tool -> generate metadata
    workflow.add_edge("run_ipfs_tool", "generate_metadata")

    # Generate metadata -> create metadata
    workflow.add_edge("generate_metadata", "create_metadata")

    # Create metadata -> negotiate terms
    workflow.add_edge("create_metadata", "negotiate_terms")

    # Negotiate terms -> mint and register IP
    workflow.add_edge("negotiate_terms", "mint_register_ip")

    # Mint and register IP -> mint license tokens
    workflow.add_edge("mint_register_ip", "mint_license_tokens")

    # Mint license tokens -> END
    workflow.add_edge("mint_license_tokens", END)

    # Compile the graph with the memory saver if provided
    return workflow.compile(checkpointer=memory)
