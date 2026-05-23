from typing import TypedDict
from langgraph.graph import StateGraph, END

class SprayState(TypedDict):
    specs: dict
    validated: bool
    compliance_report: str

def validate_specs(state: SprayState):
    required = ['pressure_rating_bar', 'nozzle_material_certification']
    valid = all(k in state['specs'] for k in required)
    return {'validated': valid, 'compliance_report': 'Validated' if valid else 'Missing specs'}

def approval_step(state: SprayState):
    return {'compliance_report': 'Approved for procurement'}

graph = StateGraph(SprayState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
