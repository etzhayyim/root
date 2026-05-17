from typing import TypedDict
from langgraph.graph import StateGraph, END

class SurgicalTrayState(TypedDict):
    spec_data: dict
    validation_results: list
    is_compliant: bool

def validate_material(state: SurgicalTrayState):
    material = state['spec_data'].get('material', '')
    is_valid = material in ['Medical Grade Stainless Steel', 'Silicone', 'PPSU']
    return {'validation_results': [f'Material check: {is_valid}'], 'is_compliant': is_valid}

def check_compliance(state: SurgicalTrayState):
    return 'compliant' if state['is_compliant'] else 'non-compliant'

graph = StateGraph(SurgicalTrayState)
graph.add_node('validate_material', validate_material)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', END)
graph = graph.compile()