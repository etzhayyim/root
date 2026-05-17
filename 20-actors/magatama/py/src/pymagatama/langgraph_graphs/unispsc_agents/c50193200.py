from typing import TypedDict
from langgraph.graph import StateGraph, END

class SaladProcurementState(TypedDict):
    delivery_temp: float
    shelf_life_days: int
    haccp_compliant: bool
    approved: bool

def validate_cold_chain(state: SaladProcurementState):
    state['approved'] = state['delivery_temp'] <= 5.0 and state['haccp_compliant']
    return state

graph = StateGraph(SaladProcurementState)
graph.add_node('validate', validate_cold_chain)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()