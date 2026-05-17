from typing import TypedDict
from langgraph.graph import StateGraph, END

class PitchProcessingState(TypedDict):
    viscosity: float
    softening_point: float
    compliance_ok: bool

def validate_pitch_specs(state: PitchProcessingState):
    state['compliance_ok'] = state['viscosity'] > 50.0 and state['softening_point'] > 80.0
    return state

def check_hazard_level(state: PitchProcessingState):
    print('Checking hazardous materials transport documentation...')
    return state

graph = StateGraph(PitchProcessingState)
graph.add_node('validate', validate_pitch_specs)
graph.add_node('safety', check_hazard_level)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()