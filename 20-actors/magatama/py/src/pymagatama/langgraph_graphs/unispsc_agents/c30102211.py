from typing import TypedDict
from langgraph.graph import StateGraph, END

class BronzePlateState(TypedDict):
    alloy_spec: str
    thickness: float
    qc_passed: bool

def validate_specs(state: BronzePlateState):
    # Business logic for bronze plate validation
    if state['thickness'] > 0:
        state['qc_passed'] = True
    return state

graph_builder = StateGraph(BronzePlateState)
graph_builder.add_node('validate', validate_specs)
graph_builder.set_entry_point('validate')
graph_builder.add_edge('validate', END)
graph = graph_builder.compile()
