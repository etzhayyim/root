from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    specs: dict
    is_compliant: bool

def validate_materials(state: ProcurementState):
    # Logic to verify material safety and surface finish standards
    state['is_compliant'] = 'non-toxic' in state['specs'].get('certifications', [])
    return state

def check_dimensions(state: ProcurementState):
    # Logic to verify dimension constraints
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_materials', validate_materials)
graph.add_node('check_dimensions', check_dimensions)
graph.add_edge('validate_materials', 'check_dimensions')
graph.add_edge('check_dimensions', END)
graph.set_entry_point('validate_materials')
graph = graph.compile()
