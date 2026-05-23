from typing import TypedDict
from langgraph.graph import StateGraph, END

class RefrigerationState(TypedDict):
    temp_range: str
    calibration_status: bool
    validation_complete: bool

def validate_specs(state: RefrigerationState):
    # Business logic for medical cold storage audit
    state['validation_complete'] = state['temp_range'] == '2-8C' and state['calibration_status']
    return 'VALIDATED' if state['validation_complete'] else 'REJECTED'

graph = StateGraph(RefrigerationState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
