from typing import TypedDict
from langgraph.graph import StateGraph, END

class BrakeState(TypedDict):
    pressure_specs: dict
    compliance_docs: list
    is_validated: bool

def validate_pressure_safety(state: BrakeState):
    pressure = state['pressure_specs'].get('bar', 0)
    return {'is_validated': pressure > 0 and pressure < 500}

def check_compliance(state: BrakeState):
    return {'compliance_docs': ['ISO_CERT', 'SAFETY_DATA_SHEET']}

graph = StateGraph(BrakeState)
graph.add_node('validate', validate_pressure_safety)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()