from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ForgingState(TypedDict):
    part_id: str
    specs: dict
    validation_passed: bool
    error_logs: List[str]

def validate_specs(state: ForgingState):
    required = ['material_grade', 'tensile_strength']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def structural_integrity_check(state: ForgingState):
    if state['validation_passed']:
        print('Performing structural analysis...')
    return state

graph = StateGraph(ForgingState)
graph.add_node('validation', validate_specs)
graph.add_node('analysis', structural_integrity_check)
graph.set_entry_point('validation')
graph.add_edge('validation', 'analysis')
graph.add_edge('analysis', END)
app = graph.compile()
