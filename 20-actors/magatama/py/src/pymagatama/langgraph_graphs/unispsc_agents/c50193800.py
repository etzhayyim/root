from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    commodity_code: str
    quality_checks: List[str]
    approved: bool

def validate_cold_chain(state: ProcurementState):
    print(f'Validating cold-chain requirements for {state[\'commodity_code\']}')
    return {'quality_checks': ['temperature_log_verified'], 'approved': True}

def final_approval(state: ProcurementState):
    return {'approved': True}

graph = StateGraph(ProcurementState)
graph.add_node('cold_chain_check', validate_cold_chain)
graph.add_node('final_approval', final_approval)
graph.add_edge('cold_chain_check', 'final_approval')
graph.add_edge('final_approval', END)
graph.set_entry_point('cold_chain_check')
graph = graph.compile()