from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product_id: str
    batch_number: str
    temp_log: List[float]
    is_compliant: bool

def validate_cold_chain(state: ProcurementState):
    # Validate temperature logs for pituitary hormones
    compliant = all(2 <= t <= 8 for t in state['temp_log'])
    return {'is_compliant': compliant}

def final_check(state: ProcurementState):
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_temp', validate_cold_chain)
graph.add_node('verify_batch', final_check)
graph.set_entry_point('validate_temp')
graph.add_edge('validate_temp', 'verify_batch')
graph.add_edge('verify_batch', END)
graph = graph.compile()