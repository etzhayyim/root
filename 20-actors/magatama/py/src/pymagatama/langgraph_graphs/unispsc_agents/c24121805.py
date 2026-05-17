from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SteelCanState(TypedDict):
    capacity_liters: float
    material_grade: str
    is_airtight: bool
    validation_errors: List[str]

def validate_spec(state: SteelCanState) -> SteelCanState:
    errors = []
    if state['capacity_liters'] <= 0:
        errors.append('Invalid capacity')
    if not state['is_airtight']:
        errors.append('Airtight seal required for steel cans')
    return {**state, 'validation_errors': errors}

def route_by_validation(state: SteelCanState) -> str:
    return 'END' if not state['validation_errors'] else 'END'

graph = StateGraph(SteelCanState)
graph.add_node('validate', validate_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()