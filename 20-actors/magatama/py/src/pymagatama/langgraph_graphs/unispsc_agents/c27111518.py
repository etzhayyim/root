from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolState(TypedDict):
    tool_id: str
    crimp_force_kn: float
    status: str

def validate_crimp_pressure(state: ToolState):
    state['status'] = 'verified' if state['crimp_force_kn'] > 0 else 'failed'
    return state

def route_verification(state: ToolState):
    return 'end' if state['status'] == 'verified' else 'end'

graph = StateGraph(ToolState)
graph.add_node('validate', validate_crimp_pressure)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()