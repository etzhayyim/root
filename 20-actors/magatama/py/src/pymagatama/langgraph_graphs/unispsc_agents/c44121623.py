from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LetterOpenerState(TypedDict):
    specs: dict
    validation_passed: bool
    error_logs: List[str]

def validate_specs(state: LetterOpenerState):
    required = ['blade_material', 'power_source']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def process_procurement(state: LetterOpenerState):
    if state['validation_passed']:
        print('Processing Letter Opener Purchase Request')
    return {'error_logs': ['Validation Success']}

graph = StateGraph(LetterOpenerState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
