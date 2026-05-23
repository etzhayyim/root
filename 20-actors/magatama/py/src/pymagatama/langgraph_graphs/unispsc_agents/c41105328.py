from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BlotState(TypedDict):
    product_id: str
    storage_temp: float
    qc_passed: bool
    steps: List[str]

def validate_storage(state: BlotState):
    if state['storage_temp'] <= -20.0:
        return {'qc_passed': True, 'steps': ['temp_validated']}
    return {'qc_passed': False, 'steps': ['temp_rejection']}

def process_batch(state: BlotState):
    return {'steps': state['steps'] + ['batch_verified']}

graph = StateGraph(BlotState)
graph.add_node('validate', validate_storage)
graph.add_node('process', process_batch)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
