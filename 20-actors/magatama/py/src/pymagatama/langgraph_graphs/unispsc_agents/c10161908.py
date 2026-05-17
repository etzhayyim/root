from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class FeedState(TypedDict):
    batch_id: str
    composition: dict
    quality_status: str
    validation_logs: List[str]

def validate_quality(state: FeedState) -> FeedState:
    moisture = state['composition'].get('moisture', 0)
    if moisture > 14.0:
        state['quality_status'] = 'REJECTED'
        state['validation_logs'].append('High moisture content detected.')
    else:
        state['quality_status'] = 'PASSED'
    return state

def route_by_status(state: FeedState) -> str:
    return 'process' if state['quality_status'] == 'PASSED' else END

def process_batch(state: FeedState) -> FeedState:
    state['validation_logs'].append('Batch processing complete.')
    return state

graph = StateGraph(FeedState)
graph.add_node('validate', validate_quality)
graph.add_node('process', process_batch)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_status)
graph.add_edge('process', END)
graph = graph.compile()