from typing import TypedDict
from langgraph.graph import StateGraph, END

class RailCarState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: list

def validate_specs(state: RailCarState):
    valid = 'safety_cert' in state['specs'] and state['specs'].get('fire_rating') == 'A'
    return {'is_compliant': valid, 'validation_log': ['Safety and Fire checks complete']}

def approve_procurement(state: RailCarState):
    return {'validation_log': state['validation_log'] + ['Procurement approved for high-value asset']}

graph = StateGraph(RailCarState)
graph.add_node('validator', validate_specs)
graph.add_node('approver', approve_procurement)
graph.set_entry_point('validator')
graph.add_edge('validator', 'approver')
graph.add_edge('approver', END)
graph = graph.compile()
