from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LemonPureeState(TypedDict):
    batch_id: str
    brix: float
    ph: float
    is_compliant: bool
    history: List[str]

def quality_check(state: LemonPureeState):
    # Business logic for validation
    if 8.0 <= state['brix'] <= 12.0 and 2.0 <= state['ph'] <= 2.5:
        return {'is_compliant': True, 'history': state['history'] + ['QC Passed']}
    return {'is_compliant': False, 'history': state['history'] + ['QC Failed']}

def cold_chain_verification(state: LemonPureeState):
    # Logic for cold chain audit
    return {'history': state['history'] + ['Cold Chain Verified']}

graph = StateGraph(LemonPureeState)
graph.add_node('qc', quality_check)
graph.add_node('cold_chain', cold_chain_verification)
graph.set_entry_point('qc')
graph.add_edge('qc', 'cold_chain')
graph.add_edge('cold_chain', END)
graph = graph.compile()