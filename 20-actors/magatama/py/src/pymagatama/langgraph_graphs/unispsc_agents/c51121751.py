from langgraph.graph import StateGraph, END
from typing import TypedDict
class DrugState(TypedDict):
    batch_id: str
    purity_level: float
    compliance_docs: bool
    approved: bool
def validate_quality(state: DrugState):
    state['approved'] = state['purity_level'] >= 99.0 and state['compliance_docs']
    return state
graph = StateGraph(DrugState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()