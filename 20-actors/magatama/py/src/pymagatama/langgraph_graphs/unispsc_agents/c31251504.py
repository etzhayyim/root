from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_pressure_rating(state: ActuatorState):
    pressure = state['specs'].get('pressure', 0)
    if pressure > 1.0:
        state['validation_errors'].append('Pressure exceeds safety limit')
    return {'is_compliant': len(state['validation_errors']) == 0}

def route_by_spec(state: ActuatorState):
    return 'validate' if state['specs'] else END

graph = StateGraph(ActuatorState)
graph.add_node('validate', validate_pressure_rating)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
