from typing import TypedDict
from langgraph.graph import StateGraph, END

class BrushProcurementState(TypedDict):
    spec_data: dict
    is_validated: bool
    compliance_report: str

def validate_material(state: BrushProcurementState):
    bristle = state['spec_data'].get('bristle_type', '').lower()
    state['is_validated'] = bristle in ['nylon', 'brass', 'steel', 'polypropylene']
    state['compliance_report'] = 'Material validation passed' if state['is_validated'] else 'Invalid material'
    return state

def finalize_spec(state: BrushProcurementState):
    state['compliance_report'] += ' - Inspection criteria finalized.'
    return state

graph = StateGraph(BrushProcurementState)
graph.add_node('validate', validate_material)
graph.add_node('finalize', finalize_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
