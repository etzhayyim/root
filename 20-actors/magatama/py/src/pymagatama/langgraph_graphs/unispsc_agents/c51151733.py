from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product_id: str
    quality_docs: List[str]
    is_approved: bool

def validate_gmp(state: ProcurementState):
    state['is_approved'] = 'GMP' in state['quality_docs']
    return state

def check_purity(state: ProcurementState):
    print(f'Checking purity for {state['product_id']}')
    return {'is_approved': state['is_approved']}

graph = StateGraph(ProcurementState)
graph.add_node('validate_gmp', validate_gmp)
graph.add_node('check_purity', check_purity)
graph.set_entry_point('validate_gmp')
graph.add_edge('validate_gmp', 'check_purity')
graph.add_edge('check_purity', END)
app = graph.compile()