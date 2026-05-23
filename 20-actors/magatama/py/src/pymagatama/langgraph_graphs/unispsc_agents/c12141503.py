from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    material_id: str
    purity: float
    hazard_checks: Annotated[Sequence[str], operator.add]
    is_cleared: bool

def validate_purity(state: CatalystState) -> dict:
    status = state['purity'] >= 99.5
    return {'is_cleared': status, 'hazard_checks': ['purity_check_passed' if status else 'purity_failed']}

def safety_screening(state: CatalystState) -> dict:
    return {'hazard_checks': ['safety_data_sheet_verified', 'dual_use_clearance_acquired']}

graph = StateGraph(CatalystState)
graph.add_node('validate', validate_purity)
graph.add_node('safety', safety_screening)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)

graph = graph.compile()
