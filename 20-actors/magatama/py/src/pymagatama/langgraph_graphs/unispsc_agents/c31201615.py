from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ActivationState(TypedDict):
    chemical_composition: str
    flash_point: float
    safety_clearance: bool

def validate_chemistry(state: ActivationState):
    if 'acetone' in state['chemical_composition'].lower():
        state['safety_clearance'] = True
    return state

def check_hazard(state: ActivationState):
    state['safety_clearance'] = state['flash_point'] > 20.0
    return state

graph = StateGraph(ActivationState)
graph.add_node('validate', validate_chemistry)
graph.add_node('safety', check_hazard)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
