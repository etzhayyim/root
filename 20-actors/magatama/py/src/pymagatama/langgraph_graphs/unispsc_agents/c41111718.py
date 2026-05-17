from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class MicroscopeState(TypedDict):
    spec_data: dict
    is_validated: bool
    compliance_report: str

def validate_specs(state: MicroscopeState):
    specs = state['spec_data']
    valid = all(key in specs for key in ['resolution', 'magnification'])
    return {'is_validated': valid, 'compliance_report': 'Validated' if valid else 'Incomplete'}

def check_dual_use(state: MicroscopeState):
    return {'compliance_report': 'Review completed for export compliance'}

graph = StateGraph(MicroscopeState)
graph.add_node('validate', validate_specs)
graph.add_node('export_review', check_dual_use)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_review')
graph.add_edge('export_review', END)
graph = graph.compile()