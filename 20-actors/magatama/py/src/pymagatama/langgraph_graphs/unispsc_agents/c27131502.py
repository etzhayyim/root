from typing import TypedDict
from langgraph.graph import StateGraph, END

class AirGunState(TypedDict):
    pressure: float
    safety_rating: bool
    compliant: bool

def validate_specs(state: AirGunState):
    state['compliant'] = state['pressure'] <= 1.0 and state['safety_rating'] is True
    return state

def check_compliance(state: AirGunState):
    return 'compliant' if state['compliant'] else 'non_compliant'

graph = StateGraph(AirGunState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph.compile()