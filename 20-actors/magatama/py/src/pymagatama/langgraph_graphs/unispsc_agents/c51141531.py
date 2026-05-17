from langgraph.graph import StateGraph, END
from typing import TypedDict
class PharmaState(TypedDict):
    purity_check: bool
    compliance_docs: bool
    storage_validated: bool
def validate_purity(state: PharmaState):
    state['purity_check'] = True
    return state
def verify_compliance(state: PharmaState):
    state['compliance_docs'] = True
    return state
def finalize_order(state: PharmaState):
    state['storage_validated'] = True
    return 'COMPLETED'
graph = StateGraph(PharmaState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('verify_compliance', verify_compliance)
graph.add_node('finalize_order', finalize_order)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'verify_compliance')
graph.add_edge('verify_compliance', 'finalize_order')
graph.add_edge('finalize_order', END)
graph.compile()