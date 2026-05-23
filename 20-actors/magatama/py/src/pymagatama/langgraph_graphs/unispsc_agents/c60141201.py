from typing import TypedDict
from langgraph.graph import StateGraph, END

class EquipmentState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_safety_standards(state: EquipmentState):
    standards = state['spec_data'].get('safety_standards', [])
    is_compliant = 'EN1176' in standards or 'ASTM_F1487' in standards
    return {'is_compliant': is_compliant}

def structural_check(state: EquipmentState):
    load = state['spec_data'].get('load_capacity', 0)
    return {'is_compliant': state['is_compliant'] and load > 50}

graph = StateGraph(EquipmentState)
graph.add_node('safety_check', validate_safety_standards)
graph.add_node('load_check', structural_check)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'load_check')
graph.add_edge('load_check', END)
graph = graph.compile()
