from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    item_name: str
    storage_temp: str
    compliance_docs: List[str]
    status: str

def validate_cold_chain(state: ProcurementState):
    state['status'] = 'validation_complete' if state['storage_temp'] == '2-8C' else 'rejected'
    return state

def verify_regulations(state: ProcurementState):
    if 'FDA_approval' in state['compliance_docs']:
        state['status'] = 'approved'
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_cold_chain', validate_cold_chain)
graph.add_node('verify_regulations', verify_regulations)
graph.set_entry_point('validate_cold_chain')
graph.add_edge('validate_cold_chain', 'verify_regulations')
graph.add_edge('verify_regulations', END)
graph = graph.compile()