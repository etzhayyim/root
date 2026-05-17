from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class EquipmentState(TypedDict): n equipment_list: List[str] n inspection_required: bool n approved_items: List[str]

def validate_equipment(state: EquipmentState):
    approved = [item for item in state['equipment_list'] if 'certified' in item.lower()]
    return {'approved_items': approved, 'inspection_required': len(approved) < len(state['equipment_list'])}

def route_inspection(state: EquipmentState):
    return 'inspect' if state['inspection_required'] else 'finish'

graph = StateGraph(EquipmentState)
graph.add_node('validate', validate_equipment)
graph.add_node('inspect', lambda s: s)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_inspection, {'inspect': 'inspect', 'finish': END})
graph.add_edge('inspect', END)