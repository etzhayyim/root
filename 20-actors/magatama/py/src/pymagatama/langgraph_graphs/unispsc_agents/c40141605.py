from typing import TypedDict
from langgraph.graph import StateGraph, END

class ValveState(TypedDict):
    pressure_rating: float
    material_compliance: bool
    validation_passed: bool

def validate_valve_specs(state: ValveState):
    if state['pressure_rating'] > 0 and state['material_compliance']:
        return {'validation_passed': True}
    return {'validation_passed': False}

graph = StateGraph(ValveState)
graph.add_node('validate', validate_valve_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
