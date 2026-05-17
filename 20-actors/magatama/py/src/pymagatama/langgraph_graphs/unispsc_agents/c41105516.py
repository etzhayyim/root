from typing import TypedDict
from langgraph.graph import StateGraph, END

class RNAExtractionState(TypedDict):
    purity_check: float
    temp_compliance: bool
    final_report: str

def validate_purity(state: RNAExtractionState):
    is_pure = state['purity_check'] >= 1.8
    return {'final_report': 'Passed' if is_pure else 'Failed'}

def check_storage(state: RNAExtractionState):
    return {'temp_compliance': True}

graph = StateGraph(RNAExtractionState)
graph.add_node('validate', validate_purity)
graph.add_node('storage', check_storage)
graph.add_edge('storage', 'validate')
graph.add_edge('validate', END)
graph.set_entry_point('storage')