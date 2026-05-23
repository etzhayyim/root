from typing import TypedDict
from langgraph.graph import StateGraph, END

class AsphaltState(TypedDict):
    temp: float
    viscosity: float
    approved: bool

def validate_asphalt(state: AsphaltState):
    state['approved'] = 140 <= state['temp'] <= 180 and state['viscosity'] > 50
    return state

graph = StateGraph(AsphaltState)
graph.add_node('validate', validate_asphalt)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
