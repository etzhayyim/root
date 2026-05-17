from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class CrudeState(TypedDict):
    api_gravity: float
    sulfur_content: float
    origin: str
    validation_passed: bool
    log: Annotated[list, operator.add]

def validate_quality(state: CrudeState) -> CrudeState:
    passed = state['api_gravity'] > 20 and state['sulfur_content'] < 0.5
    return {'validation_passed': passed, 'log': [f'Quality check: {passed}']}

def compliance_check(state: CrudeState) -> CrudeState:
    is_safe = state['origin'] not in ['restricted_zone_A', 'restricted_zone_B']
    return {'validation_passed': is_safe and state['validation_passed'], 'log': [f'Compliance check: {is_safe}']}

graph = StateGraph(CrudeState)
graph.add_node('quality', validate_quality)
graph.add_node('compliance', compliance_check)
graph.add_edge('quality', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('quality')
graph = graph.compile()