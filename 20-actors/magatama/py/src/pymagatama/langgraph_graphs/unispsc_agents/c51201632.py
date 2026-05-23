from typing import TypedDict
from langgraph.graph import StateGraph, END

class VaccineState(TypedDict):
    batch_id: str
    temperature_logs: list
    validation_status: bool

def validate_cold_chain(state: VaccineState):
    temp_ok = all(t >= 2 and t <= 8 for t in state['temperature_logs'])
    return {'validation_status': temp_ok}

def process_lot(state: VaccineState):
    print(f'Processing batch {state['batch_id']}')
    return {'validation_status': True}

graph = StateGraph(VaccineState)
graph.add_node('cold_chain_check', validate_cold_chain)
graph.add_node('batch_verification', process_lot)
graph.add_edge('cold_chain_check', 'batch_verification')
graph.add_edge('batch_verification', END)
graph.set_entry_point('cold_chain_check')
compiled_graph = graph.compile()
