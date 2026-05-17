from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class LubricantState(TypedDict):
    spec_sheet: dict
    validation_results: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_viscosity(state: LubricantState):
    val = state['spec_sheet'].get('kinematic_viscosity_cst', 0)
    status = 'PASS' if 50 <= val <= 500 else 'FAIL'
    return {'validation_results': [f'Viscosity: {status}']}

def check_flash_point(state: LubricantState):
    fp = state['spec_sheet'].get('flash_point_celsius', 0)
    status = 'PASS' if fp >= 200 else 'FAIL'
    return {'validation_results': [f'FlashPoint: {status}']}

def finalize_check(state: LubricantState):
    passed = all('PASS' in res for res in state['validation_results'])
    return {'is_approved': passed}

builder = StateGraph(LubricantState)
builder.add_node('viscosity', validate_viscosity)
builder.add_node('flash_point', check_flash_point)
builder.add_node('finalize', finalize_check)
builder.set_entry_point('viscosity')
builder.add_edge('viscosity', 'flash_point')
builder.add_edge('flash_point', 'finalize')
builder.add_edge('finalize', END)
graph = builder.compile()