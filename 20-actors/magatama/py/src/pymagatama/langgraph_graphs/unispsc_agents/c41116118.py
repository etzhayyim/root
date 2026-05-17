from typing import TypedDict
from langgraph.graph import StateGraph, END

class FoodTestSpec(TypedDict):
    lot_number: str
    expiry_date: str
    temp_req: str
    validation_status: bool

def validate_kits(state: FoodTestSpec):
    state['validation_status'] = bool(state['lot_number'] and state['expiry_date'])
    return state

def check_temp(state: FoodTestSpec):
    # logic to verify cold chain storage requirements
    return {'validation_status': state['temp_req'] == '2-8C'}

graph = StateGraph(FoodTestSpec)
graph.add_node('validate', validate_kits)
graph.add_node('cold_chain', check_temp)
graph.set_entry_point('validate')
graph.add_edge('validate', 'cold_chain')
graph.add_edge('cold_chain', END)
graph = graph.compile()