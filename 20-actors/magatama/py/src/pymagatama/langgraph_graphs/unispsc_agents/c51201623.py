from typing import TypedDict
from langgraph.graph import StateGraph, END

class VaccineState(TypedDict):
    lot_number: str
    temperature_logs: list
    expiry_date: str
    is_validated: bool

def validate_cold_chain(state: VaccineState):
    if all(2 <= temp <= 8 for temp in state['temperature_logs']):
        return {'is_validated': True}
    raise ValueError('Cold chain breach detected')

def check_expiry(state: VaccineState):
    # Business logic for expiry validation
    return {'is_validated': True}

graph = StateGraph(VaccineState)
graph.add_node('validate_cold_chain', validate_cold_chain)
graph.add_node('check_expiry', check_expiry)
graph.add_edge('validate_cold_chain', 'check_expiry')
graph.add_edge('check_expiry', END)
graph.set_entry_point('validate_cold_chain')
graph = graph.compile()
