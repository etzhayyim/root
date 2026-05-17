from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LabwareState(TypedDict):
    material: str
    volume: float
    has_certification: bool
    approved: bool

def validate_material(state: LabwareState):
    # Simulate material compliance check for lab-grade glass
    state['approved'] = state['material'] in ['borosilicate', 'plastic']
    return state

def check_certification(state: LabwareState):
    if state.get('approved') and state.get('has_certification'):
        print('Verification: Passed')
    else:
        state['approved'] = False
    return state

graph = StateGraph(LabwareState)
graph.add_node('validate', validate_material)
graph.add_node('certify', check_certification)
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph.set_entry_point('validate')
graph = graph.compile()