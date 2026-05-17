from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product_name: str
    quality_docs: list
    is_compliant: bool

def validate_gmp(state: ProcurementState):
    # Simulate GMP validation logic
    state['is_compliant'] = 'gmp_cert' in state['quality_docs']
    return 'check_purity'

def check_purity(state: ProcurementState):
    return 'end'

graph = StateGraph(ProcurementState)
graph.add_node('validate_gmp', validate_gmp)
graph.add_node('check_purity', check_purity)
graph.set_entry_point('validate_gmp')
graph.add_edge('validate_gmp', 'check_purity')
graph.add_edge('check_purity', END)

compiled_graph = graph.compile()