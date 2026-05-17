from typing import TypedDict
from langgraph.graph import StateGraph, END

class HastelloyState(TypedDict):
    part_id: str
    compliance_docs: list[str]
    passed: bool

def validate_material(state: HastelloyState):
    print(f'Checking material specs for {state[\'part_id\']}')
    return {'passed': True}

def check_bonding(state: HastelloyState):
    print('Verifying bonding integrity via NDT protocols')
    return {'passed': state['passed'] and True}

graph = StateGraph(HastelloyState)
graph.add_node('material_validation', validate_material)
graph.add_node('bonding_verification', check_bonding)
graph.add_edge('material_validation', 'bonding_verification')
graph.add_edge('bonding_verification', END)
graph.set_entry_point('material_validation')
graph = graph.compile()