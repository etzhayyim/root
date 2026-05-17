from typing import TypedDict
from langgraph.graph import StateGraph, END

class EquipmentState(TypedDict):
    item_name: str
    specs: dict
    is_compliant: bool

def validate_specs(state: EquipmentState):
    state['is_compliant'] = 'Anti-fog' in state['specs'] and 'UV_rating' in state['specs']
    return state

def route_procurement(state: EquipmentState):
    return 'compliant' if state['is_compliant'] else 'reject'

graph = StateGraph(EquipmentState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph.compile()