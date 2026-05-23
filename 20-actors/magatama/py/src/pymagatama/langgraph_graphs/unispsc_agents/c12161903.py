from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class ResinState(TypedDict):
    material_id: str
    quality_metrics: dict
    validation_passed: bool
    logs: Annotated[List[str], operator.add]

def validate_material_purity(state: ResinState) -> ResinState:
    purity = state['quality_metrics'].get('purity', 0)
    passed = purity >= 99.5
    return {'validation_passed': passed, 'logs': [f'Purity check: {passed}']}

def check_compliance(state: ResinState) -> ResinState:
    if state['validation_passed']:
        return {'logs': ['Compliance check: Passed']}
    return {'logs': ['Compliance check: Failed']}

graph = StateGraph(ResinState)
graph.add_node('validate', validate_material_purity)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
