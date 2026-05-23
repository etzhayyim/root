from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AirManifoldState(TypedDict):
    spec_sheet: dict
    validation_errors: List[str]
    is_approved: bool

def validate_pressure_rating(state: AirManifoldState):
    pressure = state['spec_sheet'].get('pressure', 0)
    if pressure < 0: state['validation_errors'].append('Invalid pressure')
    return {'is_approved': pressure > 0}

graph = StateGraph(AirManifoldState)
graph.add_node('validate', validate_pressure_rating)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
