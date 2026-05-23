from typing import TypedDict
from langgraph.graph import StateGraph, END

class PumpState(TypedDict):
    spec_sheet: dict
    validation_passed: bool

def validate_pressure_rating(state: PumpState):
    pressure = state['spec_sheet'].get('max_pressure', 0)
    return {'validation_passed': pressure > 0 and pressure < 50}

graph = StateGraph(PumpState)
graph.add_node('validate_specs', validate_pressure_rating)
graph.set_entry_point('validate_specs')
graph.add_edge('validate_specs', END)
graph = graph.compile()
