from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    product_id: str
    temperature_logs: List[float]
    is_validated: bool

def validate_cold_chain(state: ProcurementState):
    valid = all(2 <= t <= 8 for t in state['temperature_logs'])
    print(f'Cold chain valid: {valid}')
    return {'is_validated': valid}

def check_compliance(state: ProcurementState):
    compliance = 'PASS' if state['is_validated'] else 'FAIL'
    print(f'Compliance status: {compliance}')
    return {'status': compliance}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()