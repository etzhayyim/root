from typing import TypedDict
from langgraph.graph import StateGraph, END

class HardwareState(TypedDict):
    part_number: str
    material_spec: str
    inspection_passed: bool

def validate_material(state: HardwareState):
    # Simulate material compliance check for interior hardware
    state['inspection_passed'] = 'lead' not in state['material_spec'].lower()
    return state

def assembly_workflow(state: HardwareState):
    print(f'Processing finial: {state['part_number']}')
    return '{'status': 'ready_for_dispatch'}'

graph = StateGraph(HardwareState)
graph.add_node('validate', validate_material)
graph.add_node('assemble', assembly_workflow)
graph.add_edge('validate', 'assemble')
graph.add_edge('assemble', END)
graph.set_entry_point('validate')
graph = graph.compile()