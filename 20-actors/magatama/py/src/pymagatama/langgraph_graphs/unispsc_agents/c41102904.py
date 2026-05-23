from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class EmbeddingState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_msds(state: EmbeddingState):
    if 'msds_compliance' not in state['spec_data']:
        state['validation_errors'].append('Missing SDS documentation')
    return state

def check_storage(state: EmbeddingState):
    temp = state['spec_data'].get('storage_temperature_range')
    if not temp: state['validation_errors'].append('Storage temp required')
    return state

graph = StateGraph(EmbeddingState)
graph.add_node('validate_msds', validate_msds)
graph.add_node('check_storage', check_storage)
graph.set_entry_point('validate_msds')
graph.add_edge('validate_msds', 'check_storage')
graph.add_edge('check_storage', END)
app = graph.compile()
