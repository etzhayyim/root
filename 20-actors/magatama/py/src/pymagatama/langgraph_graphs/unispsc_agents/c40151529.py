from typing import TypedDict
from langgraph.graph import StateGraph, END

class PumpState(TypedDict):
    viscosity: float
    chemical_compatibility: bool
    approved: bool

def validate_pump_spec(state: PumpState):
    state['approved'] = state['viscosity'] < 5000 and state['chemical_compatibility']
    return {'approved': state['approved']}

graph = StateGraph(PumpState)
graph.add_node('validate', validate_pump_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()