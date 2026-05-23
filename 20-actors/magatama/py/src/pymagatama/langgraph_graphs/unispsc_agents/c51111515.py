from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_name: str
    purity: float
    storage_temp: float
    authorized_vendor: bool

def validate_chemistry(state: ProcurementState):
    assert state['purity'] >= 0.98, 'Purity too low'
    return {'status': 'validated'}

def check_hazmat_protocol(state: ProcurementState):
    return {'protocol': 'cold_chain_required'}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_chemistry)
graph.add_node('hazmat', check_hazmat_protocol)
graph.add_edge('validate', 'hazmat')
graph.add_edge('hazmat', END)
graph.set_entry_point('validate')
app = graph.compile()
