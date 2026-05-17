from typing import TypedDict
from langgraph.graph import StateGraph, END

class MultimeterState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: MultimeterState):
    required = ['safety_rating_cat', 'calibration_certificate']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing safety or calibration data'}

def finalize_order(state: MultimeterState):
    print('Order processed for high-precision multimeter')
    return {}

graph = StateGraph(MultimeterState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)