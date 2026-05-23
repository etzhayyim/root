from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EquipmentState(TypedDict):
    item_name: str
    specs: dict
    is_compliant: bool

def validate_specs(state: EquipmentState):
    required = ['material', 'durability_grade']
    compliance = all(k in state['specs'] for k in required)
    return {'is_compliant': compliance}

def finalize_order(state: EquipmentState):
    return {'is_compliant': True if state['is_compliant'] else False}

graph = StateGraph(EquipmentState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
