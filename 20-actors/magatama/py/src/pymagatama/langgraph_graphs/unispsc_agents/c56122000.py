from typing import TypedDict
from langgraph.graph import StateGraph, END

class LabFurnitureState(TypedDict):
    specs: dict
    is_compliant: bool

def validate_specs(state: LabFurnitureState):
    required = ['chemical_resistance', 'load_capacity']
    return {'is_compliant': all(k in state['specs'] for k in required)}

def proceed_order(state: LabFurnitureState):
    return {'is_compliant': True}

graph = StateGraph(LabFurnitureState)
graph.add_node('validate', validate_specs)
graph.add_node('order', proceed_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'order')
graph.add_edge('order', END)
graph = graph.compile()