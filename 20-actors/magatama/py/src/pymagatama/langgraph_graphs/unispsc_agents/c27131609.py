from typing import TypedDict
from langgraph.graph import StateGraph, END

class SilencerState(TypedDict):
    spec: dict
    validated: bool
    error_log: list

def validate_specs(state: SilencerState):
    required = ['Connection Port Size', 'Maximum Operating Pressure']
    errors = [f'Missing {f}' for f in required if f not in state['spec']]
    return {'validated': len(errors) == 0, 'error_log': errors}

def process_workflow(state: SilencerState):
    if state['validated']:
        print('Proceeding to technical procurement review.')
    return state

graph = StateGraph(SilencerState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_workflow)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
