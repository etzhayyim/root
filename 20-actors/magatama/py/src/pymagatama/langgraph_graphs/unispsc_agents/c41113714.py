from typing import TypedDict
from langgraph.graph import StateGraph, END

class DiffState(TypedDict):
    specs: dict
    validated: bool
    error_log: list

def validate_specs(state: DiffState):
    required = ['Bandwidth', 'Accuracy Percentage']
    errors = [f'Missing {s}' for s in required if s not in state['specs']]
    return {'validated': len(errors) == 0, 'error_log': errors}

def process_workflow(state: DiffState):
    if state['validated']:
        print('Configuring Differentiator settings...')
    return state

graph_builder = StateGraph(DiffState)
graph_builder.add_node('validation', validate_specs)
graph_builder.add_node('config', process_workflow)
graph_builder.set_entry_point('validation')
graph_builder.add_edge('validation', 'config')
graph_builder.add_edge('config', END)
graph = graph_builder.compile()
