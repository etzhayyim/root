from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RivetToolState(TypedDict):
    tool_name: str
    specs: dict
    is_compliant: bool

def validate_specs(state: RivetToolState):
    hardness = state['specs'].get('blade_hardness_hrc', 0)
    state['is_compliant'] = hardness >= 55
    return state

def check_safety(state: RivetToolState):
    return "compliant" if state['is_compliant'] else "non_compliant"

graph = StateGraph(RivetToolState)
graph.add_node("validation", validate_specs)
graph.set_entry_point("validation")
graph.add_edge("validation", END)
graph = graph.compile()
