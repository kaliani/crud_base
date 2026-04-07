from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from agent.utils.state import AgentState
from agent.utils.nodes import assistant
from agent.utils.tools import tools

builder = StateGraph(AgentState)

builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "assistant")
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")

graph = builder.compile()
