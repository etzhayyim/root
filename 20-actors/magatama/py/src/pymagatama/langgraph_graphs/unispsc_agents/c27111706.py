from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolState(TypedDict):
    tool_type: str
    material_spec: str
    torque_rating: float
    is_compliant: bool

def validate_spec(state: ToolState):
    state['is_compliant'] = state['material_spec'] == 'Cr-V' and state['torque_rating'] > 0
    return state

def generate_report(state: ToolState):
    return {'status': 'Approved' if state['is_compliant'] else 'Rejected'}

graph = StateGraph(ToolState)
graph.add_node('validate', validate_spec)
graph.add_node('report', generate_report)
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph.set_entry_point('validate')
graph = graph.compile()
