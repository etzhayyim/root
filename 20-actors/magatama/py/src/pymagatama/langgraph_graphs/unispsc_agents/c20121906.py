from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    part_id: str
    specs: dict
    validation_log: List[str]
    is_approved: bool

def validate_load_capacity(state: BearingState):
    load = state['specs'].get('load_capacity_rating', 0)
    if load > 500: 
        state['validation_log'].append('High capacity verified.')
    return {'validation_log': state['validation_log']}

def check_material_compliance(state: BearingState):
    material = state['specs'].get('material', '')
    if material == 'Al-6061-T6':
        state['validation_log'].append('Material standard met.')
        state['is_approved'] = True
    return {'validation_log': state['validation_log'], 'is_approved': state['is_approved']}

graph = StateGraph(BearingState)
graph.add_node('validate_load', validate_load_capacity)
graph.add_node('check_material', check_material_compliance)
graph.add_edge('validate_load', 'check_material')
graph.add_edge('check_material', END)
graph.set_entry_point('validate_load')
compiled_graph = graph.compile()