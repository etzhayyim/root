from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    is_gmp_certified: bool
    purity_level: float
    status: str

def validate_gmp(state: ProcurementState):
    if state.get('is_gmp_certified'):
        return 'validated'
    return 'rejected'

workflow = StateGraph(ProcurementState)
workflow.add_node('check_gmp', validate_gmp)
workflow.set_entry_point('check_gmp')
workflow.add_edge('check_gmp', END)
graph = workflow.compile()