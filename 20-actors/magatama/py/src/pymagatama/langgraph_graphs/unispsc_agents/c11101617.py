from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class MetalAdditiveState(TypedDict):
    material_code: str
    purity_level: float
    safety_check_passed: bool
    log: Annotated[List[str], operator.add]

def validate_purity(state: MetalAdditiveState) -> MetalAdditiveState:
    if state['purity_level'] < 0.99:
        return {'log': ['Purity check failed: below 99% threshold']}
    return {'safety_check_passed': True, 'log': ['Purity verified']}

def perform_safety_screening(state: MetalAdditiveState) -> MetalAdditiveState:
    if state['material_code'].startswith('11'):
        return {'log': ['Material passed hazardous material screening']}
    return {'log': ['Material failed safety screening']}

graph = StateGraph(MetalAdditiveState)
graph.add_node('validate', validate_purity)
graph.add_node('screen', perform_safety_screening)
graph.add_edge('validate', 'screen')
graph.add_edge('screen', END)
graph.set_entry_point('validate')
graph = graph.compile()