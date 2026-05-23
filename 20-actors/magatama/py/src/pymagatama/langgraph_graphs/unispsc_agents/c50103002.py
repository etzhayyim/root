from typing import TypedDict
from langgraph.graph import StateGraph, END

class FrozenProduceState(TypedDict):
    temp_log: list
    is_compliant: bool

def validate_cold_chain(state: FrozenProduceState):
    # Business logic for cold chain checking
    compliant = all(t <= -18 for t in state['temp_log'])
    print(f'Temperature compliance: {compliant}')
    return {'is_compliant': compliant}

def process_shipment(state: FrozenProduceState):
    status = 'APPROVED' if state['is_compliant'] else 'REJECTED'
    print(f'Shipment status: {status}')
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(FrozenProduceState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('process', process_shipment)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
