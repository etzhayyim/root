from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    commodity_id: str
    quality_passed: bool
    temp_log: float
    status: str

def validate_cold_chain(state: ProcurementState):
    state['quality_passed'] = state['temp_log'] <= 4.0
    return {'status': 'Validated' if state['quality_passed'] else 'Rejected'}

def update_inventory(state: ProcurementState):
    return {'status': 'Inventory Updated'}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('update', update_inventory)
graph.add_edge('validate', 'update')
graph.add_edge('update', END)
graph.set_entry_point('validate')
graph = graph.compile()
