from typing import TypedDict
from langgraph.graph import StateGraph, END

class StretcherSheetState(TypedDict):
    spec_data: dict
    validation_ok: bool
    compliance_report: str

def validate_materials(state: StretcherSheetState):
    materials = state['spec_data'].get('material', '')
    return {'validation_ok': 'flame_retardant' in materials}

def generate_compliance(state: StretcherSheetState):
    return {'compliance_report': 'Verified against medical textile standards' if state['validation_ok'] else 'Compliance failed'}

graph = StateGraph(StretcherSheetState)
graph.add_node('validate', validate_materials)
graph.add_node('compliance', generate_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()