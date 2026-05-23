from langgraph.graph import StateGraph, END
from typing import TypedDict

class ConveyorState(TypedDict):
    spec_data: dict
    validation_score: float

def validate_specs(state: ConveyorState):
    # Simulate CAD/Spec validation for feeder parameters
    power = state['spec_data'].get('power', 0)
    score = 1.0 if power > 0 else 0.0
    return {'validation_score': score}

def route_by_score(state: ConveyorState):
    return 'valid' if state['validation_score'] > 0 else END

graph = StateGraph(ConveyorState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
