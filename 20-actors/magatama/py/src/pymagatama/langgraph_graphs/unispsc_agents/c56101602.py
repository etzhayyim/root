from typing import TypedDict
from langgraph.graph import StateGraph, END

class OutdoorChairState(TypedDict):
    spec_data: dict
    validation_results: list
    is_approved: bool

def validate_material(state: OutdoorChairState):
    material = state['spec_data'].get('material')
    valid = material in ['aluminum', 'synthetic_resin', 'teak', 'powder_coated_steel']
    return {'validation_results': [f'Material valid: {valid}']}

def check_durability(state: OutdoorChairState):
    rating = state['spec_data'].get('load_rating', 0)
    return {'is_approved': rating >= 150}

graph = StateGraph(OutdoorChairState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_durability', check_durability)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_durability')
graph.add_edge('check_durability', END)
graph = graph.compile()
