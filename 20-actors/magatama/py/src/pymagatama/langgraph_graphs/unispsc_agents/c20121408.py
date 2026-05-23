from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    spec: dict
    validation_results: Annotated[list[str], operator.add]
    status: str

def validate_load_capacity(state: BearingState) -> BearingState:
    spec = state['spec']
    if spec.get('load_rating_dynamic', 0) > 0:
        state['validation_results'].append('Load capacity check passed')
    else:
        state['validation_results'].append('Load capacity check failed')
    return state

def check_material_compliance(state: BearingState) -> BearingState:
    if state['spec'].get('material_grade') in ['bearing_steel', 'ceramic']:
        state['validation_results'].append('Material compliance passed')
    else:
        state['validation_results'].append('Material compliance failed')
    return state

workflow = StateGraph(BearingState)
workflow.add_node('validate_load', validate_load_capacity)
workflow.add_node('check_material', check_material_compliance)

workflow.set_entry_point('validate_load')
workflow.add_edge('validate_load', 'check_material')
workflow.add_edge('check_material', END)

graph = workflow.compile()
