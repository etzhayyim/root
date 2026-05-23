from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MountingBaseState(TypedDict):
    part_id: str
    pressure_rating: float
    material_certified: bool
    validation_log: List[str]

def validate_load_specs(state: MountingBaseState):
    if state['pressure_rating'] > 500:
        state['validation_log'].append('High pressure load validation passed.')
    else:
        state['validation_log'].append('Standard pressure load validation.')
    return {'validation_log': state['validation_log']}

def check_compliance(state: MountingBaseState):
    if state['material_certified']:
        state['validation_log'].append('Material certification verified.')
    return {'validation_log': state['validation_log']}

graph = StateGraph(MountingBaseState)
graph.add_node('validate_load', validate_load_specs)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_load')
graph.add_edge('validate_load', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()
