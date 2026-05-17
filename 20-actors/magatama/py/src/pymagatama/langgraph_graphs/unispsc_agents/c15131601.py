from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class AluminumState(TypedDict):
    alloy_grade: str
    quality_checks: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_alloy_grade(state: AluminumState) -> AluminumState:
    # Logic to validate Aerospace grade aluminum spec compliance
    state['is_compliant'] = state['alloy_grade'] in ['7075-T6', '2024-T3']
    return state

def run_inspection_logic(state: AluminumState) -> AluminumState:
    # Simulate material property verification
    state['quality_checks'] = ['tensile_test_passed', 'ultrasonic_scan_complete']
    return state

builder = StateGraph(AluminumState)
builder.add_node('validate', validate_alloy_grade)
builder.add_node('inspect', run_inspection_logic)
builder.add_edge('validate', 'inspect')
builder.add_edge('inspect', END)
builder.set_entry_point('validate')
graph = builder.compile()