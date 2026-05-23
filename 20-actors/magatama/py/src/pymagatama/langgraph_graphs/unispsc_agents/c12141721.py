from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class EnzymeState(TypedDict):
    commodity_code: str
    quality_metrics: dict
    workflow_steps: List[str]
    validation_status: bool

def validate_purity(state: EnzymeState) -> EnzymeState:
    purity = state['quality_metrics'].get('purity', 0)
    state['validation_status'] = purity >= 99.0
    state['workflow_steps'].append('purity_checked')
    return state

def cold_chain_verification(state: EnzymeState) -> EnzymeState:
    temp = state['quality_metrics'].get('storage_temp', 25)
    if temp <= 4.0:
        state['workflow_steps'].append('cold_chain_verified')
    return state

graph = StateGraph(EnzymeState)
graph.add_node('validate', validate_purity)
graph.add_node('cold_chain', cold_chain_verification)
graph.set_entry_point('validate')
graph.add_edge('validate', 'cold_chain')
graph.add_edge('cold_chain', END)

# The graph instance is ready for compilation
# compiled_graph = graph.compile()
