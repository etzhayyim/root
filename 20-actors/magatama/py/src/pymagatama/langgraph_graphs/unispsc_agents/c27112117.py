from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolSpecState(TypedDict):
    tool_id: str
    material: str
    hrc_rating: float
    qc_passed: bool

def validate_pliers(state: ToolSpecState):
    state['qc_passed'] = state['hrc_rating'] >= 55.0
    return state

def check_compliance(state: ToolSpecState):
    return 'approved' if state['qc_passed'] else 'rejected'

graph = StateGraph(ToolSpecState)
graph.add_node('validate', validate_pliers)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
