from typing import TypedDict
from langgraph.graph import StateGraph, END

class LabwareState(TypedDict):
    material: str
    volume: float
    is_sterile: bool
    validation_passed: bool

def validate_specs(state: LabwareState):
    state['validation_passed'] = state['volume'] > 0 and state['material'] in ['Glass', 'Plastic']
    return state

def check_sterility(state: LabwareState):
    if state['is_sterile']:
        print('Verification: Sterility certificate confirmed.')
    return state

graph = StateGraph(LabwareState)
graph.add_node('validate', validate_specs)
graph.add_node('sterility', check_sterility)
graph.set_entry_point('validate')
graph.add_edge('validate', 'sterility')
graph.add_edge('sterility', END)
graph = graph.compile()