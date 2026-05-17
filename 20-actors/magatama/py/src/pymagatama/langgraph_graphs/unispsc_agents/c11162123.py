from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    batch_id: str
    purity_level: float
    compliance_passed: bool
    steps: Annotated[Sequence[str], operator.add]

def validate_purity(state: CatalystState) -> CatalystState:
    passed = state['purity_level'] >= 99.5
    return {'compliance_passed': passed, 'steps': ['purity_validation']}

def check_compliance(state: CatalystState) -> CatalystState:
    return {'compliance_passed': state['compliance_passed'] and True, 'steps': ['compliance_check']}

def create_procurement_graph():
    graph = StateGraph(CatalystState)
    graph.add_node('validate', validate_purity)
    graph.add_node('compliance', check_compliance)
    graph.set_entry_point('validate')
    graph.add_edge('validate', 'compliance')
    graph.add_edge('compliance', END)
    return graph.compile()