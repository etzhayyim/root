from typing import TypedDict
from langgraph.graph import StateGraph, END

class IncubatorState(TypedDict):
    temp: float
    rpm: int
    is_calibrated: bool

def validate_specs(state: IncubatorState):
    if state['temp'] < 4 or state['temp'] > 60: return {'status': 'OUT_OF_RANGE'}
    return {'status': 'VALID'}

def check_compliance(state: IncubatorState):
    return {'compliant': state['is_calibrated']}

graph = StateGraph(IncubatorState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()