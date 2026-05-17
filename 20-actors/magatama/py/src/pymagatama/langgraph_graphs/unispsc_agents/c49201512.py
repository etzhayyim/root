from typing import TypedDict
from langgraph.graph import StateGraph, END

class FitnessEquipmentState(TypedDict):
    item_name: str
    specs: dict
    approved: bool

def validate_rope_specs(state: FitnessEquipmentState):
    rope = state['specs']
    if 'length' in rope and 'material' in rope:
        state['approved'] = True
    return state

graph = StateGraph(FitnessEquipmentState)
graph.add_node('validate', validate_rope_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()