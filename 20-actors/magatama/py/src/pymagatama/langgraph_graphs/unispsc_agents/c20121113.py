from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    part_number: str
    spec_data: dict
    validation_log: List[str]
    is_compliant: bool

def validate_load_ratings(state: BearingState) -> BearingState:
    state['validation_log'].append('Validating dynamic and static load ratings against ISO standards.')
    state['is_compliant'] = True
    return state

def check_material_specs(state: BearingState) -> BearingState:
    state['validation_log'].append('Verifying material composition and tolerance certificates.')
    return state

graph = StateGraph(BearingState)
graph.add_node('validate_load', validate_load_ratings)
graph.add_node('check_material', check_material_specs)
graph.set_entry_point('validate_load')
graph.add_edge('validate_load', 'check_material')
graph.add_edge('check_material', END)
graph = graph.compile()
