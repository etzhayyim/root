from typing import TypedDict
from langgraph.graph import StateGraph, END

class PycnometerState(TypedDict):
    volume_ml: float
    material: str
    is_calibrated: bool
    validation_error: str

def validate_spec(state: PycnometerState):
    if state['volume_ml'] <= 0:
        return {'validation_error': 'Invalid volume'}
    return {'validation_error': None}

def check_compliance(state: PycnometerState):
    if not state['is_calibrated']:
        return {'is_calibrated': False}
    return {'is_calibrated': True}

graph = StateGraph(PycnometerState)
graph.add_node('validate', validate_spec)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()