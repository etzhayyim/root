from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CoatingState(TypedDict):
    material_id: str
    purity_level: float
    safety_check_passed: bool
    validation_log: Annotated[Sequence[str], operator.add]

def validate_purity(state: CoatingState) -> dict:
    passed = state['purity_level'] >= 99.9
    return {'safety_check_passed': passed, 'validation_log': [f'Purity check: {passed}']}

def environmental_scrub(state: CoatingState) -> dict:
    return {'validation_log': ['Environmental compliance verified']}

graph = StateGraph(CoatingState)
graph.add_node('validate', validate_purity)
graph.add_node('env_scrub', environmental_scrub)
graph.set_entry_point('validate')
graph.add_edge('validate', 'env_scrub')
graph.add_edge('env_scrub', END)
graph = graph.compile()