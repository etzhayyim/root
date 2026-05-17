from langgraph.graph import StateGraph, END
from typing import TypedDict

class MeatProcurementState(TypedDict):
    temperature: float
    sanitary_cert: str
    is_compliant: bool

def validate_cold_chain(state: MeatProcurementState):
    state['is_compliant'] = state['temperature'] <= -18.0
    return state

def check_certification(state: MeatProcurementState):
    if not state.get('sanitary_cert'):
        state['is_compliant'] = False
    return state

graph = StateGraph(MeatProcurementState)
graph.add_node('cold_chain', validate_cold_chain)
graph.add_node('cert_check', check_certification)
graph.set_entry_point('cold_chain')
graph.add_edge('cold_chain', 'cert_check')
graph.add_edge('cert_check', END)
graph = graph.compile()