from typing import TypedDict
from langgraph.graph import StateGraph, END

class ElectricalState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_specs(state: ElectricalState):
    # Business logic for electrical component compliance
    required_keys = ['voltage', 'certification', 'ip_rating']
    state['is_compliant'] = all(k in state['spec_data'] for k in required_keys)
    return state

def route_by_compliance(state: ElectricalState):
    return 'compliant' if state['is_compliant'] else 'flag_for_review'

graph = StateGraph(ElectricalState)
graph.add_node('validation', validate_specs)
graph.add_edge('validation', END)
graph.set_entry_point('validation')
