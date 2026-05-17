from typing import TypedDict
from langgraph.graph import StateGraph, END

class ShoeProcurementState(TypedDict):
    material: str
    size: str
    safety_compliant: bool

def validate_material(state: ShoeProcurementState):
    return {'safety_compliant': 'leather' in state['material'].lower() or 'synthetic' in state['material'].lower()}

def check_size(state: ShoeProcurementState):
    print(f'Validating size {state['size']}')
    return {}

graph = StateGraph(ShoeProcurementState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_size', check_size)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_size')
graph.add_edge('check_size', END)
graph = graph.compile()