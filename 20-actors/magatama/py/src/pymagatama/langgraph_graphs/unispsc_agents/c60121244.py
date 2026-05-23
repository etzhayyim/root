from typing import TypedDict
from langgraph.graph import StateGraph, END
class StretcherState(TypedDict):
    material_specs: dict
    compliance_ok: bool
    final_report: str
def validate_materials(state: StretcherState):
    is_valid = state['material_specs'].get('tensile_strength', 0) > 500
    return {'compliance_ok': is_valid}
def generate_validation_report(state: StretcherState):
    report = 'Approved' if state['compliance_ok'] else 'Rejected'
    return {'final_report': report}
graph = StateGraph(StretcherState)
graph.add_node('validate', validate_materials)
graph.add_node('report', generate_validation_report)
graph.set_entry_point('validate')
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph = graph.compile()
