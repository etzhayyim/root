from langgraph.graph import StateGraph, END
from typing import TypedDict
class SilverNitrateState(TypedDict):
    purity: float
    hazard_verified: bool
    compliance_docs: list
    status: str
def validate_specs(state: SilverNitrateState):
    state['hazard_verified'] = state['purity'] >= 99.0
    state['status'] = 'validation_complete' if state['hazard_verified'] else 'failed_purity_test'
    return state
graph = StateGraph(SilverNitrateState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()
