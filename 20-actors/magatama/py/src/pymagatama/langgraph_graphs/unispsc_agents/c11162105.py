from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    batch_id: str
    purity_level: float
    steps: List[str]
    approved: bool

def validate_batch(state: ProcessingState) -> ProcessingState:
    if state['purity_level'] > 0.99:
        state['steps'].append('Validation Success')
        state['approved'] = True
    else:
        state['steps'].append('Validation Failed')
        state['approved'] = False
    return state

def process_material(state: ProcessingState) -> ProcessingState:
    if state['approved']:
        state['steps'].append('Material Processing')
    return state

graph = StateGraph(ProcessingState)
graph.add_node('validate', validate_batch)
graph.add_node('process', process_material)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()