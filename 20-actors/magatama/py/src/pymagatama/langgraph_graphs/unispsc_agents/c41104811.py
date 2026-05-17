from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_spec(state: ProcessingState):
    fields = ['flow_rate', 'resolution']
    valid = all(key in state['spec_data'] for key in fields)
    return {'validation_passed': valid}

def route_by_validation(state: ProcessingState):
    return 'process' if state['validation_passed'] else END

def process_fractionator(state: ProcessingState):
    print('Processing density gradient data...')
    return {'validation_passed': True}

graph = StateGraph(ProcessingState)
graph.add_node('validate', validate_spec)
graph.add_node('process', process_fractionator)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
graph = graph.compile()