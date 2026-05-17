from typing import TypedDict
from langgraph.graph import StateGraph, END

class TractorSpecState(TypedDict):
    horsepower: float
    emission_standard: str
    is_compliant: bool

def validate_specs(state: TractorSpecState):
    is_compliant = state['horsepower'] > 50 and state['emission_standard'] == 'Stage V'
    return {'is_compliant': is_compliant}

def approve_order(state: TractorSpecState):
    return {'status': 'Approved' if state['is_compliant'] else 'Rejected'}

graph = StateGraph(TractorSpecState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approve_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()