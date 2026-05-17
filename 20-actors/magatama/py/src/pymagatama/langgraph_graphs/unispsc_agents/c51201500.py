from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    drug_name: str
    temperature_logs: List[float]
    compliance_docs: List[str]
    is_approved: bool

def validate_cold_chain(state: ProcurementState) -> dict:
    is_safe = all(2.0 <= t <= 8.0 for t in state['temperature_logs'])
    print(f'Cold chain status: {is_safe}')
    return {'is_approved': is_safe}

def verify_regulations(state: ProcurementState) -> dict:
    has_docs = len(state['compliance_docs']) >= 3
    return {'is_approved': state['is_approved'] and has_docs}

graph = StateGraph(ProcurementState)
graph.add_node('validate_cold_chain', validate_cold_chain)
graph.add_node('verify_regulations', verify_regulations)
graph.set_entry_point('validate_cold_chain')
graph.add_edge('validate_cold_chain', 'verify_regulations')
graph.add_edge('verify_regulations', END)
graph = graph.compile()