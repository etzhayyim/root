from typing import TypedDict
from langgraph.graph import StateGraph, END

class TubingState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_pressure(state: TubingState):
    pressure = state['specs'].get('max_pressure', 0)
    return {'validated': pressure > 0, 'error': '' if pressure > 0 else 'Invalid Pressure'}

def check_compliance(state: TubingState):
    has_cert = state['specs'].get('certification')
    return {'validated': state['validated'] and bool(has_cert)}

graph = StateGraph(TubingState)
graph.add_node('validate', validate_pressure)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()