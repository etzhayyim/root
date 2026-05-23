from typing import TypedDict
from langgraph.graph import StateGraph, END

class PearlState(TypedDict):
    pearl_specs: dict
    validation_passed: bool

def validate_pearl_quality(state: PearlState):
    specs = state['pearl_specs']
    is_valid = specs.get('luster') in ['AAA', 'AA'] and specs.get('diameter') > 5.0
    return {'validation_passed': is_valid}

def route_by_validation(state: PearlState):
    return 'process' if state['validation_passed'] else END

def process_procurement(state: PearlState):
    print('Processing high-value pearl procurement...')
    return {'validation_passed': True}

graph = StateGraph(PearlState)
graph.add_node('validate', validate_pearl_quality)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
graph = graph.compile()
