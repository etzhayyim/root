from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    purity_level: float
    storage_temp: float
    status: str

def validate_quality(state: ProcurementState):
    if state['purity_level'] < 99.0:
        return {'status': 'rejected'}
    return {'status': 'validated'}

def check_cold_chain(state: ProcurementState):
    if state['storage_temp'] > 25.0:
        return {'status': 'spoiled'}
    return {'status': 'ready'}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_quality)
graph.add_node('cold_chain', check_cold_chain)
graph.set_entry_point('validate')
graph.add_edge('validate', 'cold_chain')
graph.add_edge('cold_chain', END)
graph = graph.compile()