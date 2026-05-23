from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    catalyst_id: str
    purity_level: float
    safety_check_passed: bool
    validation_log: Annotated[Sequence[str], operator.add]

def validate_purity(state: CatalystState) -> CatalystState:
    if state['purity_level'] < 0.98:
        return {'validation_log': ['Purity level below standard: 98% required.']}
    return {'safety_check_passed': True, 'validation_log': ['Purity validation passed.']}

def safety_compliance_check(state: CatalystState) -> CatalystState:
    if not state.get('safety_check_passed'):
        return {'validation_log': ['Compliance check failed: Safety protocols missing.']}
    return {'validation_log': ['Safety protocols verified.']}

def build_graph():
    graph = StateGraph(CatalystState)
    graph.add_node('validate_purity', validate_purity)
    graph.add_node('safety_compliance', safety_compliance_check)
    graph.set_entry_point('validate_purity')
    graph.add_edge('validate_purity', 'safety_compliance')
    graph.add_edge('safety_compliance', END)
    return graph.compile()

graph = build_graph()
