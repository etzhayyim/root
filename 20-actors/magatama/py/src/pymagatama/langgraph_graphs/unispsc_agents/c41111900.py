from typing import TypedDict
from langgraph.graph import StateGraph, END

class InstrumentState(TypedDict):
    instrument_type: str
    calibration_required: bool
    is_calibrated: bool
    validation_passed: bool

def validate_instrument(state: InstrumentState):
    return {'validation_passed': True} if state['is_calibrated'] else {'validation_passed': False}

def route_verification(state: InstrumentState):
    return 'validate' if state['calibration_required'] else 'finish'

graph = StateGraph(InstrumentState)
graph.add_node('validate', validate_instrument)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()