from typing import TypedDict
from langgraph.graph import StateGraph, END

class PipeState(TypedDict):
    diameter: float
    thickness: float
    material: str
    is_compliant: bool

def validate_specs(state: PipeState):
    # Business logic for industrial copper piping validation
    if state['diameter'] > 0 and state['thickness'] > 0:
        state['is_compliant'] = True
    else:
        state['is_compliant'] = False
    return state

graph = StateGraph(PipeState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()