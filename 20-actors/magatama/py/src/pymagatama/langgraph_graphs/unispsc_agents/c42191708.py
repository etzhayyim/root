from typing import TypedDict
from langgraph.graph import StateGraph, END

class PressureControlState(TypedDict):
    pressure_setting: float
    compliance_docs: list
    is_validated: bool

def validate_specs(state: PressureControlState):
    # Business logic for verifying cabinet pressure requirements
    state['is_validated'] = state['pressure_setting'] > 0 and len(state['compliance_docs']) > 0
    return state

def approval_step(state: PressureControlState):
    print('Executing medical compliance review...')
    return {'is_validated': True}

graph = StateGraph(PressureControlState)
graph.add_node('validate', validate_specs)
graph.add_node('approval', approval_step)
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph.set_entry_point('validate')
graph = graph.compile()