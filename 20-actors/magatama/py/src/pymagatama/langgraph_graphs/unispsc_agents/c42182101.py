from typing import TypedDict
from langgraph.graph import StateGraph, END

class StethoscopeState(TypedDict):
    model_id: str
    calibration_data: dict
    compliance_docs: list
    is_approved: bool

def validate_specs(state: StethoscopeState):
    # Simulate verification of medical grade electronic signal specs
    state['is_approved'] = 'Frequency_Range' in state['calibration_data'] and len(state['compliance_docs']) > 0
    return state

def route_by_compliance(state: StethoscopeState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(StethoscopeState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()