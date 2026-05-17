from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    purity_level: float
    compliant: bool

def validate_purity(state: ProcurementState):
    state['compliant'] = state['purity_level'] >= 99.0
    return state

def log_result(state: ProcurementState):
    print(f'Batch {state['batch_id']} compliance: {state['compliant']}')
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('log', log_result)
graph.set_entry_point('validate')
graph.add_edge('validate', 'log')
graph.add_edge('log', END)
graph = graph.compile()