from langgraph.graph import StateGraph, END
from typing import TypedDict

class RollerProcurementState(TypedDict):
    spec_data: dict
    validation_result: bool

def validate_load_capacity(state: RollerProcurementState):
    capacity = state['spec_data'].get('load_capacity', 0)
    state['validation_result'] = capacity > 0
    return state

def check_compliance(state: RollerProcurementState):
    return state

graph = StateGraph(RollerProcurementState)
graph.add_node('validate_capacity', validate_load_capacity)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_capacity')
graph.add_edge('validate_capacity', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()
