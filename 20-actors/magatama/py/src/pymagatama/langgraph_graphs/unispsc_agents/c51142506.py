from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product_name: str
    quality_docs: List[str]
    compliance_cleared: bool

def validate_gmp(state: ProcurementState):
    state['compliance_cleared'] = 'GMP_Certificate' in state.get('quality_docs', [])
    return 'COMPLIANCE_CHECK_PASSED' if state['compliance_cleared'] else 'COMPLIANCE_ERROR'

def finalize_procurement(state: ProcurementState): return {}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_gmp)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
