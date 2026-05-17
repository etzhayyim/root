from typing import TypedDict
from langgraph.graph import StateGraph, END

class MCCState(TypedDict):
    specs: dict
    validated: bool
    compliance_report: str

def validate_specs(state: MCCState):
    required_keys = ['voltage', 'current', 'ip_rating']
    valid = all(key in state['specs'] for key in required_keys)
    return {'validated': valid, 'compliance_report': 'Validated' if valid else 'Missing specs'}

def generate_procurement_workflow():
    graph = StateGraph(MCCState)
    graph.add_node('validate', validate_specs)
    graph.set_entry_point('validate')
    graph.add_edge('validate', END)
    return graph.compile()