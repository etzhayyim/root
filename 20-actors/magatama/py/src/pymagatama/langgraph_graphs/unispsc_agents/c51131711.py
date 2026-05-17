from typing import TypedDict
from langgraph.graph import StateGraph, END

class TenecteplaseState(TypedDict):
    batch_id: str
    temp_log: float
    status: str

def validate_cold_chain(state: TenecteplaseState):
    if state['temp_log'] <= 8.0:
        return {'status': 'VALIDATED'}
    return {'status': 'REJECTED'}

def process_batch(state: TenecteplaseState):
    print(f'Processing pharmaceutical batch: {state['batch_id']}')
    return {'status': 'COMPLETED'}

graph = StateGraph(TenecteplaseState)
graph.add_node('cold_chain', validate_cold_chain)
graph.add_node('process', process_batch)
graph.set_entry_point('cold_chain')
graph.add_edge('cold_chain', 'process')
graph.add_edge('process', END)
graph = graph.compile()