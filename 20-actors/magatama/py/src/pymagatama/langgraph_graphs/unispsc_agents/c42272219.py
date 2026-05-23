from typing import TypedDict
from langgraph.graph import StateGraph, END

class VentilatorFilterState(TypedDict):
    bfe_rating: float
    vfe_rating: float
    is_sterile: bool
    compliance_checked: bool

def validate_specs(state: VentilatorFilterState):
    if state['bfe_rating'] > 99.9 and state['vfe_rating'] > 99.9:
        return {'compliance_checked': True}
    return {'compliance_checked': False}

graph = StateGraph(VentilatorFilterState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
