from typing import TypedDict
from langgraph.graph import StateGraph, END

class PhotoelasticState(TypedDict):
    instrument_model: str
    calibration_status: bool
    validation_score: float

def validate_specs(state: PhotoelasticState):
    # Simulate validation logic for optical calibration data
    state['validation_score'] = 0.95 if 'sensor' in state['instrument_model'] else 0.0
    return state

def check_compliance(state: PhotoelasticState):
    # Simulate dual-use regulatory screening
    return 'compliant' if state['validation_score'] > 0.8 else 'flagged'

graph = StateGraph(PhotoelasticState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()