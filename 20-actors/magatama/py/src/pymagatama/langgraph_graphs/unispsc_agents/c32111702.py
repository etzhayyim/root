from typing import TypedDict
from langgraph.graph import StateGraph, END

class ThyristorState(TypedDict):
    voltage_rating: float
    current_rating: float
    compliance_docs: list
    is_valid: bool

def validate_specs(state: ThyristorState):
    state['is_valid'] = state['voltage_rating'] > 0 and state['current_rating'] > 0
    return state

def check_compliance(state: ThyristorState):
    if 'RoHS' not in state['compliance_docs']:
        state['is_valid'] = False
    return state

graph = StateGraph(ThyristorState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()