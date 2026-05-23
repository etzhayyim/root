from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    specs: dict
    approved: bool

def validate_purity(state: ProcurementState):
    content = state['specs'].get('fatty_acid_content', 0)
    state['approved'] = content >= 85.0
    return state

def check_compliance(state: ProcurementState):
    print(f'Checking compliance for {state['item_name']}')
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
