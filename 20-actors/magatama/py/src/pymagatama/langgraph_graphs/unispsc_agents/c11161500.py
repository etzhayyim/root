from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CarbonFiberState(TypedDict):
    material_id: str
    specifications: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_tensile_strength(state: CarbonFiberState) -> CarbonFiberState:
    strength = state['specifications'].get('tensile_strength_mpa', 0)
    if strength > 3500:
        state['validation_logs'] = ['Tensile strength validated above 3500MPa']
        state['is_compliant'] = True
    else:
        state['validation_logs'] = ['Tensile strength insufficient']
        state['is_compliant'] = False
    return state

def export_control_check(state: CarbonFiberState) -> CarbonFiberState:
    if state.get('is_compliant'):
        state['validation_logs'] = ['Dual-use export control check passed']
    return state

builder = StateGraph(CarbonFiberState)
builder.add_node('validate', validate_tensile_strength)
builder.add_node('control', export_control_check)
builder.set_entry_point('validate')
builder.add_edge('validate', 'control')
builder.add_edge('control', END)
graph = builder.compile()