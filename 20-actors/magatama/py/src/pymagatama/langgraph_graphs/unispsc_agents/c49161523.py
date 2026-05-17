from langgraph.graph import StateGraph, END
from typing import TypedDict

class EquipmentState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_gear(state: EquipmentState):
    specs = state['spec_data']
    valid = specs.get('belt_mechanism') == 'velcro' and specs.get('material_strength') > 50
    return {'is_compliant': valid}

graph = StateGraph(EquipmentState)
graph.add_node('validate', validate_gear)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()