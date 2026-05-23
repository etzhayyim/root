from typing import TypedDict
from langgraph.graph import StateGraph, END

class FilmState(TypedDict):
    film_type: str
    batch_id: str
    is_refrigerated: bool
    compliant: bool

def validate_cold_chain(state: FilmState):
    state['compliant'] = state['is_refrigerated']
    return 'process_batch'

def process_batch(state: FilmState):
    print(f'Processing batch {state['batch_id']} for compliance')
    return state

graph = StateGraph(FilmState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('process_batch', process_batch)
graph.set_entry_point('validate')
graph.add_edge('process_batch', END)
graph = graph.compile()
