from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from operator import add

class AdditiveState(TypedDict):
    purity_level: float
    safety_check_passed: bool
    process_steps: Annotated[Sequence[str], add]

def validate_purity(state: AdditiveState):
    passed = state['purity_level'] >= 99.9
    return {'safety_check_passed': passed, 'process_steps': ['Purity Verification']}

def process_additive(state: AdditiveState):
    if state['safety_check_passed']:
        return {'process_steps': ['Standard Stabilization', 'Containerization']}
    return {'process_steps': ['Quarantine for Re-refining']}

graph = StateGraph(AdditiveState)
graph.add_node('validate', validate_purity)
graph.add_node('process', process_additive)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()
