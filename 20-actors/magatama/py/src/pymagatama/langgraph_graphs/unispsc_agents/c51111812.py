from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrugProcurementState(TypedDict):
    batch_number: str
    quality_docs: dict
    shipping_compliant: bool

def validate_gmp(state: DrugProcurementState):
    state['quality_docs']['gmp_verified'] = True
    return state

def check_storage(state: DrugProcurementState):
    state['shipping_compliant'] = True
    return state

graph = StateGraph(DrugProcurementState)
graph.add_node('validate_gmp', validate_gmp)
graph.add_node('check_storage', check_storage)
graph.set_entry_point('validate_gmp')
graph.add_edge('validate_gmp', 'check_storage')
graph.add_edge('check_storage', END)
graph = graph.compile()
