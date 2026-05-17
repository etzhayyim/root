from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PlasmaProcurementState(TypedDict):
    batch_id: str
    compliance_docs: List[str]
    temperature_logs: bool
    is_approved: bool

def validate_gmp(state: PlasmaProcurementState):
    state['is_approved'] = 'GMP_Cert' in state['compliance_docs']
    return state

def check_temp(state: PlasmaProcurementState):
    if state['is_approved']:
        state['is_approved'] = state['temperature_logs']
    return state

graph = StateGraph(PlasmaProcurementState)
graph.add_node('validate_gmp', validate_gmp)
graph.add_node('check_temp', check_temp)
graph.set_entry_point('validate_gmp')
graph.add_edge('validate_gmp', 'check_temp')
graph.add_edge('check_temp', END)
compiled_graph = graph.compile()