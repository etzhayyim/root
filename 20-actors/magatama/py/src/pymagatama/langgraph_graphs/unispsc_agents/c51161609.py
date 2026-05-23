from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    purity_level: float
    gmp_certified: bool
    validation_passed: bool

def validate_chemistry(state: ProcurementState):
    state['validation_passed'] = state['purity_level'] >= 99.0 and state['gmp_certified']
    return {'validation_passed': state['validation_passed']}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_chemistry)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
