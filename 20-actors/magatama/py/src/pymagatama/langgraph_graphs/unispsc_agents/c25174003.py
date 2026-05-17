from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RadiatorSpecState(TypedDict):
    part_number: str
    pressure_rating: float
    verified: bool
    errors: List[str]

def validate_pressure(state: RadiatorSpecState):
    if state['pressure_rating'] < 88.0: 
        return {'verified': False, 'errors': ['Pressure rating below safety threshold']}
    return {'verified': True}

graph = StateGraph(RadiatorSpecState)
graph.add_node('validate_spec', validate_pressure)
graph.set_entry_point('validate_spec')
graph.add_edge('validate_spec', END)
graph = graph.compile()