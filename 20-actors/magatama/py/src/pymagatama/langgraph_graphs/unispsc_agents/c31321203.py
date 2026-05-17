from langgraph.graph import StateGraph, END
from typing import TypedDict

class HastelloyState(TypedDict):
    material_spec: dict
    weld_inspection: bool
    is_compliant: bool

def validate_materials(state: HastelloyState):
    compliance = state['material_spec'].get('alloy') == 'Hastelloy X'
    return {'is_compliant': compliance}

def check_welds(state: HastelloyState):
    passed = state.get('weld_inspection', False)
    return {'is_compliant': state['is_compliant'] and passed}

graph = StateGraph(HastelloyState)
graph.add_node('validate', validate_materials)
graph.add_node('weld_check', check_welds)
graph.add_edge('validate', 'weld_check')
graph.add_edge('weld_check', END)
graph.set_entry_point('validate')
graph = graph.compile()