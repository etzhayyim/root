from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

class CarbonFiberState(TypedDict):
    spec: dict
    validation_results: Annotated[list, operator.add]
    status: str

def validate_tensile_strength(state: CarbonFiberState):
    strength = state['spec'].get('tensile_strength_mpa', 0)
    if strength > 3000:
        return {'validation_results': ['Strength validation passed']}
    return {'validation_results': ['Strength validation failed']}

def structural_integrity_check(state: CarbonFiberState):
    return {'status': 'CERTIFIED' if 'Strength validation passed' in state['validation_results'] else 'REJECTED'}

builder = StateGraph(CarbonFiberState)
builder.add_node('validate', validate_tensile_strength)
builder.add_node('integrity', structural_integrity_check)
builder.add_edge('validate', 'integrity')
builder.add_edge('integrity', END)
builder.set_entry_point('validate')
graph = builder.compile()