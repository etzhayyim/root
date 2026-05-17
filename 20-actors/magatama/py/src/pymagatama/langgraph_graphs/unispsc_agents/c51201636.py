from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class VaccineState(TypedDict):
    batch_id: str
    temp_log: List[float]
    is_compliant: bool

def validate_cold_chain(state: VaccineState):
    state['is_compliant'] = all(2.0 <= t <= 8.0 for t in state['temp_log'])
    return state

def route_by_compliance(state: VaccineState):
    return 'process' if state['is_compliant'] else 'reject'

graph = StateGraph(VaccineState)
graph.add_node('validate', validate_cold_chain)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()