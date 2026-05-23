from typing import TypedDict
from langgraph.graph import StateGraph, END

class PipeState(TypedDict):
    material_grade: str
    spec_compliant: bool
    clearance_approved: bool

def validate_material(state: PipeState):
    state['spec_compliant'] = state['material_grade'].startswith('Nickel-')
    return state

def check_export_controls(state: PipeState):
    state['clearance_approved'] = state['spec_compliant']
    return state

graph = StateGraph(PipeState)
graph.add_node('validate', validate_material)
graph.add_node('export_check', check_export_controls)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)

app = graph.compile()
