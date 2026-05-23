from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    item_name: str
    compliance_docs: List[str]
    is_cold_chain_valid: bool
    status: str

def validate_pharma_specs(state: ProcurementState):
    if all(doc in state['compliance_docs'] for doc in ['GMP', 'COA']):
        return {'status': 'VALIDATED'}
    return {'status': 'REJECTED'}

def check_cold_chain(state: ProcurementState):
    return {'is_cold_chain_valid': True}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_pharma_specs)
graph.add_node('cold_chain', check_cold_chain)
graph.set_entry_point('validate')
graph.add_edge('validate', 'cold_chain')
graph.add_edge('cold_chain', END)
graph = graph.compile()
