from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BatikWaxState(TypedDict):
    wax_type: str
    melting_point: float
    purity_level: str
    is_compliant: bool

def validate_wax_specs(state: BatikWaxState):
    # Business logic for batik wax quality control
    if 60.0 <= state['melting_point'] <= 85.0:
        return {'is_compliant': True}
    return {'is_compliant': False}

graph = StateGraph(BatikWaxState)
graph.add_node('validator', validate_wax_specs)
graph.set_entry_point('validator')
graph.add_edge('validator', END)
graph = graph.compile()