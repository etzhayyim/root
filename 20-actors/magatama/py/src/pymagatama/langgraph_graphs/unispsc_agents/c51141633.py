from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DrugState(TypedDict):
    batch_id: str
    purity_level: float
    requires_cold_chain: bool
    compliance_passed: bool

def validate_purity(state: DrugState) -> dict:
    passed = state['purity_level'] >= 99.5
    return {'compliance_passed': passed}

def check_storage(state: DrugState) -> dict:
    return {'requires_cold_chain': True}

graph = StateGraph(DrugState)
graph.add_node('validate', validate_purity)
graph.add_node('storage_check', check_storage)
graph.set_entry_point('validate')
graph.add_edge('validate', 'storage_check')
graph.add_edge('storage_check', END)
graph = graph.compile()