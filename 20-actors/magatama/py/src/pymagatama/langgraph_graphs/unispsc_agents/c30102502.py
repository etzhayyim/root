from typing import TypedDict
from langgraph.graph import StateGraph, END

class AlloyState(TypedDict):
    material_spec: dict
    compliance_report: str
    approved: bool

def validate_composition(state: AlloyState):
    # Simulate CAD/Spec verification logic
    is_valid = state['material_spec'].get('purity') > 99.5
    return {'compliance_report': 'Passed' if is_valid else 'Failed', 'approved': is_valid}

def process_export_check(state: AlloyState):
    # Dual-use export control routing
    return {'compliance_report': state['compliance_report'] + ' - Export Review Cleared'}

graph = StateGraph(AlloyState)
graph.add_node('validation', validate_composition)
graph.add_node('export_check', process_export_check)
graph.set_entry_point('validation')
graph.add_edge('validation', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()