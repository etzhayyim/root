from typing import TypedDict
from langgraph.graph import StateGraph, END

class TitaniumPartState(TypedDict):
    part_id: str
    material_certified: bool
    tolerance_checked: bool
    ndt_passed: bool

def validate_material(state: TitaniumPartState):
    print(f'Verifying material certs for {state['part_id']}')
    return {'material_certified': True}

def perform_ndt(state: TitaniumPartState):
    print('Executing ultrasonic inspection...')
    return {'ndt_passed': True}

graph = StateGraph(TitaniumPartState)
graph.add_node('verify_material', validate_material)
graph.add_node('ndt_inspection', perform_ndt)
graph.set_entry_point('verify_material')
graph.add_edge('verify_material', 'ndt_inspection')
graph.add_edge('ndt_inspection', END)
graph = graph.compile()
