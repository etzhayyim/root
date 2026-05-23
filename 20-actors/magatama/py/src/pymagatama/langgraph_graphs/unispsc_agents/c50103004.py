from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    temp_history: list[float]
    brix: float
    passed: bool

def validate_cold_chain(state: ProcurementState):
    is_safe = all(temp <= -18.0 for temp in state['temp_history'])
    return {'passed': is_safe}

workflow = StateGraph(ProcurementState)
workflow.add_node('validate', validate_cold_chain)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
