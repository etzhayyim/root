from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class BloodCollectionState(TypedDict):
    device_id: str
    batch_id: str
    flow_rate: float
    status: str
    validation_logs: List[str]

def validate_flow(state: BloodCollectionState):
    if 10.0 <= state['flow_rate'] <= 100.0:
        return {'status': 'FLOW_OK', 'validation_logs': state['validation_logs'] + ['Flow rate validated.']}
    return {'status': 'FLOW_FAIL', 'validation_logs': state['validation_logs'] + ['Critical flow rate error.']}

def process_batch(state: BloodCollectionState):
    return {'status': 'COMPLETED', 'validation_logs': state['validation_logs'] + ['Batch processing secured.']}

graph = StateGraph(BloodCollectionState)
graph.add_node('validate', validate_flow)
graph.add_node('process', process_batch)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)

# Compilation
graph = graph.compile()