from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class BallScrewState(TypedDict):
    specs: dict
    validation_results: Annotated[list[str], operator.add]
    is_compliant: bool

def validate_specs(state: BallScrewState) -> BallScrewState:
    specs = state['specs']
    results = []
    if specs.get('load_rating', 0) < 5000:
        results.append('Load capacity below industrial threshold.')
    return {'validation_results': results, 'is_compliant': len(results) == 0}

def route_verification(state: BallScrewState) -> str:
    return 'compliant' if state['is_compliant'] else 'reject'

graph = StateGraph(BallScrewState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
