from typing import TypedDict
from langgraph.graph import StateGraph, END

class EquipmentState(TypedDict):
    item_name: str
    safety_standards: list[str]
    needs_inspection: bool

def validate_equipment(state: EquipmentState):
    state['needs_inspection'] = 'ASTM' not in state['safety_standards']
    return 'validating'

def perform_inspection(state: EquipmentState):
    return f'Inspection required for {state['item_name']}'

graph = StateGraph(EquipmentState)
graph.add_node('validate', validate_equipment)
graph.add_node('inspect', perform_inspection)
graph.add_edge('validate', 'inspect')
graph.set_entry_point('validate')
graph.set_finish_point('inspect')
graph = graph.compile()
