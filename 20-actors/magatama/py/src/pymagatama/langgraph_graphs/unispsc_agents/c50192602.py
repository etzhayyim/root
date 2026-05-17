from typing import TypedDict
from langgraph.graph import StateGraph, END

class FoodSupplyState(TypedDict):
    product_name: str
    temp_log: float
    haccp_compliant: bool
    is_approved: bool

def validate_cold_chain(state: FoodSupplyState):
    state['is_approved'] = state['temp_log'] <= -18.0 and state['haccp_compliant']
    return state

graph = StateGraph(FoodSupplyState)
graph.add_node('validate', validate_cold_chain)
graph.set_entry_point('validate')
graph.add_edge('validate', END)