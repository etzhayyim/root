from typing import TypedDict
from langgraph.graph import StateGraph, END

class PearProcurementState(TypedDict):
    origin: str
    temp_celsius: float
    inspection_passed: bool

def validate_pear_specs(state: PearProcurementState):
    if state['temp_celsius'] > 5.0:
        return {'inspection_passed': False}
    return {'inspection_passed': True}

graph = StateGraph(PearProcurementState)
graph.add_node('validate', validate_pear_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()