from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CopperOrder(TypedDict):
    specs: dict
    validation_passed: bool
    error_log: List[str]

def validate_dimensions(state: CopperOrder):
    specs = state['specs']
    passed = specs.get('tolerance', 0.1) <= 0.05
    return {'validation_passed': passed, 'error_log': [] if passed else ['Tolerance out of spec']}

def process_stamping(state: CopperOrder):
    print('Initiating industrial stamping qualification workflow...')
    return {'validation_passed': True}

graph = StateGraph(CopperOrder)
graph.add_node('validate', validate_dimensions)
graph.add_node('stamp_process', process_stamping)
graph.set_entry_point('validate')
graph.add_edge('validate', 'stamp_process')
graph.add_edge('stamp_process', END)
graph = graph.compile()