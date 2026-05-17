from typing import TypedDict
from langgraph.graph import StateGraph, END

class ControlState(TypedDict):
    spec_data: dict
    validated: bool
    error: str

def validate_specs(state: ControlState):
    required = ['input_voltage', 'output_type']
    valid = all(k in state['spec_data'] for k in required)
    return {'validated': valid, 'error': '' if valid else 'Missing required fields'}

def process_workflow(state: ControlState):
    print('Processing counter control specification...')
    return {'validated': True}

graph = StateGraph(ControlState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_workflow)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()