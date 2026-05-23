from typing import TypedDict
from langgraph.graph import StateGraph, END

class PunchingMachineState(TypedDict):
    spec_data: dict
    is_validated: bool

def validate_specs(state: PunchingMachineState):
    # Business logic for validating book puncher specs
    state['is_validated'] = state['spec_data'].get('capacity', 0) > 0
    return state

def process_workflow(state: PunchingMachineState):
    print('Processing procurement workflow for punching machine.')
    return state

graph = StateGraph(PunchingMachineState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_workflow)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
