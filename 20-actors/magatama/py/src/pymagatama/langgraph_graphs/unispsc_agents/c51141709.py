from typing import TypedDict
from langgraph.graph import StateGraph, END

class FluphenazineState(TypedDict):
    batch: str
    potency: float
    compliance_check: bool

def validate_batch(state: FluphenazineState):
    if state['potency'] >= 99.0:
        return {'compliance_check': True}
    return {'compliance_check': False}

graph = StateGraph(FluphenazineState)
graph.add_node('validate', validate_batch)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
