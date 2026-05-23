from typing import TypedDict
from langgraph.graph import StateGraph, END

class OrangePureeState(TypedDict):
    batch_id: str
    quality_passed: bool
    brix: float

def validate_quality(state: OrangePureeState):
    state['quality_passed'] = state.get('brix', 0) >= 10.0
    return 'process_batch' if state['quality_passed'] else 'reject_batch'

def process_batch(state: OrangePureeState):
    print(f'Batch {state["batch_id"]} is within specification.')
    return state

def reject_batch(state: OrangePureeState):
    print(f'Batch {state["batch_id"]} rejected due to low brix.')
    return state

graph = StateGraph(OrangePureeState)
graph.add_node('validate', validate_quality)
graph.add_node('process_batch', process_batch)
graph.add_node('reject_batch', reject_batch)
graph.set_entry_point('validate')
graph.add_edge('process_batch', END)
graph.add_edge('reject_batch', END)
graph = graph.compile()
