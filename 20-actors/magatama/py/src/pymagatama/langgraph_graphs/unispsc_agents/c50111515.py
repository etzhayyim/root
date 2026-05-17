from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChickenProcessingState(TypedDict):
    supply_chain_data: dict
    approved: bool

def validate_cold_chain(state: ChickenProcessingState):
    temp = state['supply_chain_data'].get('avg_temp', 10)
    state['approved'] = temp <= 4.0
    return state

def check_certs(state: ChickenProcessingState):
    has_certs = 'health_certificate' in state['supply_chain_data']
    state['approved'] = state['approved'] and has_certs
    return state

graph = StateGraph(ChickenProcessingState)
graph.add_node('validate_temperature', validate_cold_chain)
graph.add_node('verify_compliance', check_certs)
graph.set_entry_point('validate_temperature')
graph.add_edge('validate_temperature', 'verify_compliance')
graph.add_edge('verify_compliance', END)
graph = graph.compile()