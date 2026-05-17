from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class FuelState(TypedDict):
    commodity: str
    volume: float
    safety_clearance: bool
    compliance_report: str

def validate_safety(state: FuelState) -> FuelState:
    # Simulate safety protocol for hazardous fuel materials
    state['safety_clearance'] = state['volume'] < 1000000.0
    return state

def generate_compliance(state: FuelState) -> FuelState:
    if state['safety_clearance']:
        state['compliance_report'] = 'CLEARED_FOR_TRANSPORT'
    else:
        state['compliance_report'] = 'REQUIRES_HAZMAT_ESCALATION'
    return state

graph = StateGraph(FuelState)
graph.add_node('safety_check', validate_safety)
graph.add_node('compliance', generate_compliance)
graph.add_edge('safety_check', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('safety_check')
graph = graph.compile()