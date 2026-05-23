from typing import TypedDict
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    specs: dict
    validated: bool
    compliance_report: str

def validate_specs(state: ForgingState):
    is_valid = 'Material Grade' in state['specs'] and 'Hardness Rating' in state['specs']
    return {'validated': is_valid, 'compliance_report': 'Passed' if is_valid else 'Failed: Missing critical specs'}

def perform_ndt_check(state: ForgingState):
    return {'compliance_report': 'NDT inspection logged for forgings'}

graph = StateGraph(ForgingState)
graph.add_node('validate', validate_specs)
graph.add_node('ndt', perform_ndt_check)
graph.add_edge('validate', 'ndt')
graph.add_edge('ndt', END)
graph.set_entry_point('validate')
graph = graph.compile()
