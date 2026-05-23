from typing import TypedDict
from langgraph.graph import StateGraph, END

class LabBathState(TypedDict):
    temp_range: float
    safety_check: bool
    is_compliant: bool

def validate_specs(state: LabBathState):
    if state['temp_range'] > 0:
        return {'safety_check': True, 'is_compliant': True}
    return {'safety_check': False, 'is_compliant': False}

graph = StateGraph(LabBathState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
