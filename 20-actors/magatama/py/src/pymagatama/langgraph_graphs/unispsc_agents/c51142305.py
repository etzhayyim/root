from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrugProcurementState(TypedDict):
    purity_level: float
    gmp_certified: bool
    compliant: bool

def validate_quality(state: DrugProcurementState):
    if state['purity_level'] >= 99.0 and state['gmp_certified']:
        return {'compliant': True}
    return {'compliant': False}

graph = StateGraph(DrugProcurementState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
