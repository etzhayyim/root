from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BerryState(TypedDict):
    commodity: str
    quality_docs: List[str]
    is_compliant: bool

def validate_food_safety(state: BerryState):
    # Simulate inspection logic for processed berries
    required = ['lab_test', 'cold_chain_log']
    valid = all(doc in state['quality_docs'] for doc in required)
    return {'is_compliant': valid}

def route_by_compliance(state: BerryState):
    return 'approve' if state['is_compliant'] else END

def approve(state: BerryState):
    print('Procurement approved: Food safety standards met.')

graph = StateGraph(BerryState)
graph.add_node('validate', validate_food_safety)
graph.add_node('approve', approve)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'approve': 'approve'})
graph.add_edge('approve', END)
graph = graph.compile()
