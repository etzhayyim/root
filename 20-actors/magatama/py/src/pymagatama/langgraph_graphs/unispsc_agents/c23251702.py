from typing import TypedDict
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    spec_data: dict
    validation_result: bool
    compliance_report: str

def validate_specs(state: ForgingState):
    specs = state['spec_data']
    valid = specs.get('tonnage', 0) > 0 and 'safety_certs' in specs
    return {'validation_result': valid, 'compliance_report': 'Validated' if valid else 'Missing safety data'}

def export_check(state: ForgingState):
    return {'compliance_report': 'Screened for dual-use export control'}

graph = StateGraph(ForgingState)
graph.add_node('validate', validate_specs)
graph.add_node('export_screen', export_check)
graph.add_edge('validate', 'export_screen')
graph.add_edge('export_screen', END)
graph.set_entry_point('validate')
graph = graph.compile()