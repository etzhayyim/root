from typing import TypedDict
from langgraph.graph import StateGraph, END

class OrthoState(TypedDict):
    material_id: str
    compliance_docs: list
    validation_status: bool

def validate_material(state: OrthoState):
    is_valid = len(state['compliance_docs']) >= 3
    return {'validation_status': is_valid}

def process_procurement(state: OrthoState):
    print(f'Processing material {state['material_id']}')
    return {}

graph = StateGraph(OrthoState)
graph.add_node('validate', validate_material)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()