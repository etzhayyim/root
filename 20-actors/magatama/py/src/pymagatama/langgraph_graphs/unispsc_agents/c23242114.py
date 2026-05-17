from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_specs(state: ProcessingState):
    required = ['clamping_range_mm', 'mounting_compatibility']
    state['validated'] = all(k in state['spec_data'] for k in required)
    return state

def check_dual_use(state: ProcessingState):
    print('Checking export controls for precision steady rest...')
    return 'end_node'

graph = StateGraph(ProcessingState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_dual_use)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()