from typing import TypedDict
from langgraph.graph import StateGraph, END

class ExtractionState(TypedDict):
    kit_id: str
    purity_level: float
    qc_passed: bool

def validate_qc(state: ExtractionState) -> ExtractionState:
    state['qc_passed'] = state['purity_level'] >= 0.95
    return state

def finalize_order(state: ExtractionState) -> ExtractionState:
    return state

workflow = StateGraph(ExtractionState)
workflow.add_node('qc_check', validate_qc)
workflow.add_node('finalize', finalize_order)
workflow.add_edge('qc_check', 'finalize')
workflow.set_entry_point('qc_check')
workflow.add_edge('finalize', END)
graph = workflow.compile()
