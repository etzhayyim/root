from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolState(TypedDict):
    tool_type: str
    material: str
    diameter_range: float
    is_compliant: bool

def validate_specs(state: ToolState):
    # Basic validation for strap wrench industrial requirements
    state['is_compliant'] = state['diameter_range'] > 0 and 'strap' in state['tool_type']
    return state

graph = StateGraph(ToolState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
