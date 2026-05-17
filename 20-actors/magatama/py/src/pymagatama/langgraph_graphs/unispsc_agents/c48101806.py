from typing import TypedDict
from langgraph.graph import StateGraph, END

class KitchenwareState(TypedDict):
    material: str
    is_food_safe: bool
    validation_status: str

def validate_specs(state: KitchenwareState):
    if state['is_food_safe']:
        return {'validation_status': 'APPROVED'}
    return {'validation_status': 'REJECTED'}

def packing_logic(state: KitchenwareState):
    return {'validation_status': f'PACKED_AS_{state["material"]}'}

graph = StateGraph(KitchenwareState)
graph.add_node('validate', validate_specs)
graph.add_node('pack', packing_logic)
graph.add_edge('validate', 'pack')
graph.add_edge('pack', END)
graph.set_entry_point('validate')
graph = graph.compile()