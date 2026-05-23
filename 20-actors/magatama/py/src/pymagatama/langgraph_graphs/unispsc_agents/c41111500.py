from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WeighingInstrumentState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_calibration(state: WeighingInstrumentState):
    errors = []
    if 'calibration_certificate' not in state['specs']:
        errors.append('Missing calibration certificate')
    return {'validation_errors': errors}

def approval_check(state: WeighingInstrumentState):
    approved = len(state['validation_errors']) == 0
    return {'approved': approved}

graph = StateGraph(WeighingInstrumentState)
graph.add_node('validate', validate_calibration)
graph.add_node('approve', approval_check)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
