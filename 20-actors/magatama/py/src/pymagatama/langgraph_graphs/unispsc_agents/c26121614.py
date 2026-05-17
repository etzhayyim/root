from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CableState(TypedDict):
    specs: dict
    validated: bool
    compliance_report: str

def validate_cable(state: CableState):
    required = ['voltage', 'fire_rating']
    valid = all(k in state['specs'] for k in required)
    return {'validated': valid, 'compliance_report': 'Validated' if valid else 'Missing Specs'}

def route_by_validation(state: CableState):
    return 'process' if state['validated'] else 'reject'

graph = StateGraph(CableState)
graph.add_node('validate', validate_cable)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'process': END, 'reject': END})