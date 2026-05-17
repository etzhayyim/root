from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: ProcessingState):
    if 'power' in state['specs'] and state['specs']['power'] > 0:
        return {'validated': True}
    return {'validated': False, 'error': 'Invalid power specs'}

def route_by_safety(state: ProcessingState):
    if state['validated']:
        return 'process'
    return END

def process_machinery(state: ProcessingState):
    print('Initiating industrial machinery quality audit...')
    return {'validated': True}

graph = StateGraph(ProcessingState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_machinery)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_safety, {'process': 'process', '__end__': END})
graph.add_edge('process', END)
compile_graph = graph.compile()