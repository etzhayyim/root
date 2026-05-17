from typing import TypedDict
from langgraph.graph import StateGraph, END

class TubeState(TypedDict):
    specs: dict
    validation_passed: bool

def validate_specs(state: TubeState):
    required = ['material', 'pressure_rating']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def process_tubing(state: TubeState):
    if state['validation_passed']:
        print('Processing tubing procurement logic')
    return state

graph = StateGraph(TubeState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_tubing)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()