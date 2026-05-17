from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    cas_number: str
    purity_required: float
    test_results: List[str]
    validation_passed: bool

def validate_purity(state: ChemicalState):
    passed = state['purity_required'] >= 99.9
    return {'validation_passed': passed, 'test_results': state['test_results'] + ['Purity Validation']}

def hazardous_check(state: ChemicalState):
    return {'test_results': state['test_results'] + ['Hazmat Protocol Clearance']}

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('hazmat', hazardous_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'hazmat')
graph.add_edge('hazmat', END)
graph = graph.compile()