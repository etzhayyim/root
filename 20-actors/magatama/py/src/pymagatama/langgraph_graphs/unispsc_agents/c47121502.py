from typing import TypedDict
from langgraph.graph import StateGraph, END

class CartState(TypedDict):
    part_type: str
    is_compatible: bool
    validation_log: list

def validate_accessory(state: CartState):
    is_valid = state['part_type'] in ['trolley_tray', 'waste_bag_holder', 'mop_bucket_clip']
    return {'is_compatible': is_valid, 'validation_log': ['Compatibility check passed'] if is_valid else ['Incompatible part']}

def update_inventory(state: CartState):
    return {'validation_log': state['validation_log'] + ['Inventory updated']}

graph = StateGraph(CartState)
graph.add_node('validate', validate_accessory)
graph.add_node('inventory', update_inventory)
graph.add_edge('validate', 'inventory')
graph.add_edge('inventory', END)
graph.set_entry_point('validate')
graph = graph.compile()
