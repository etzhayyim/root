from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class VectorState(TypedDict):
    biosafety_level: int
    purity_validated: bool
    compliance_check: bool

def validate_safety(state: VectorState):
    state['compliance_check'] = state['biosafety_level'] >= 2
    return state

def process_vector_kit(state: VectorState):
    state['purity_validated'] = True
    return state

graph = StateGraph(VectorState)
graph.add_node('safety_check', validate_safety)
graph.add_node('purity_process', process_vector_kit)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'purity_process')
graph.add_edge('purity_process', END)
graph = graph.compile()
