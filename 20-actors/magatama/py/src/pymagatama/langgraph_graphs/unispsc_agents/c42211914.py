from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    spec_data: dict
    validated: bool
    compliance_report: str

def validate_med_device(state: State):
    specs = state['spec_data']
    is_valid = 'ISO_certification' in specs and 'Regulatory_Compliance_ID' in specs
    return {'validated': is_valid, 'compliance_report': 'Validated' if is_valid else 'Failed'}

graph = StateGraph(State)
graph.add_node('validate', validate_med_device)
graph.set_entry_point('validate')
graph.add_edge('validate', END)

compiled_graph = graph.compile()
