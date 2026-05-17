from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class HydrocarbonState(TypedDict):
    commodity_id: str
    purity: float
    safety_check_passed: bool
    log: Annotated[Sequence[str], operator.add]

def validate_purity(state: HydrocarbonState) -> HydrocarbonState:
    if state['purity'] < 95.0:
        return {**state, 'safety_check_passed': False, 'log': ['Purity too low']}
    return {**state, 'safety_check_passed': True, 'log': ['Purity verified']}

def route_by_safety(state: HydrocarbonState) -> str:
    return 'END' if state['safety_check_passed'] else 'END'

graph = StateGraph(HydrocarbonState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)

graph = graph.compile()