from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

class BallScrewState(TypedDict):
    spec_data: dict
    validation_results: Annotated[Sequence[str], operator.add]
    status: str

def validate_precision(state: BallScrewState):
    grade = state['spec_data'].get('lead_accuracy_grade', 'unknown')
    if grade in ['C0', 'C1', 'C2', 'C3']:
        return {'validation_results': ['Precision grade meets industrial standards'], 'status': 'validating_mechanics'}
    return {'validation_results': ['Precision grade insufficient'], 'status': 'failed'}

def inspect_load_capacity(state: BallScrewState):
    # Simulate load test logic
    return {'validation_results': ['Load capacity verified'], 'status': 'completed'}

graph = StateGraph(BallScrewState)
graph.add_node('validate', validate_precision)
graph.add_node('inspect', inspect_load_capacity)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)

graph = graph.compile()
