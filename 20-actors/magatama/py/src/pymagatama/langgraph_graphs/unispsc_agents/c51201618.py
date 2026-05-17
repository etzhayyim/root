from typing import TypedDict
from langgraph.graph import StateGraph, END

class RotavirusState(TypedDict):
    batch_id: str
    temperature_logs: list
    validation_status: bool

def validate_cold_chain(state: RotavirusState):
    # Business logic for verifying cold chain integrity
    state['validation_status'] = all(temp < 8.0 for temp in state['temperature_logs'])
    print(f'Batch {state['batch_id']} cold chain valid: {state['validation_status']}')
    return state

def check_compliance(state: RotavirusState):
    # Regulatory compliance check node
    return {'validation_status': True}

graph = StateGraph(RotavirusState)
graph.add_node('cold_chain', validate_cold_chain)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('cold_chain')
graph.add_edge('cold_chain', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()