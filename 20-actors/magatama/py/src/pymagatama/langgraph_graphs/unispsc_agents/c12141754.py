from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ResinState(TypedDict):
    material_id: str
    purity_level: float
    validation_passed: bool
    log: Annotated[Sequence[str], operator.add]

def validate_purity(state: ResinState) -> ResinState:
    passed = state['purity_level'] >= 99.999
    return {'validation_passed': passed, 'log': [f'Purity check: {passed}']}

def process_resin_spec(state: ResinState) -> ResinState:
    if state['validation_passed']:
        return {'log': ['Generating high-purity procurement spec']}
    return {'log': ['Rejecting: Purity below standard']}

graph = StateGraph(ResinState)
graph.add_node('validate', validate_purity)
graph.add_node('process', process_resin_spec)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()
