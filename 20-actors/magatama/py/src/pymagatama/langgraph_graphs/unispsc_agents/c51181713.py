from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DrugProcurementState(TypedDict):
    batch_id: str
    purity_level: float
    gmp_valid: bool
    approved: bool

def validate_quality(state: DrugProcurementState):
    state['approved'] = (state['purity_level'] >= 99.9) and state['gmp_valid']
    return state

graph_builder = StateGraph(DrugProcurementState)
graph_builder.add_node('validate', validate_quality)
graph_builder.set_entry_point('validate')
graph_builder.add_edge('validate', END)
graph = graph_builder.compile()
