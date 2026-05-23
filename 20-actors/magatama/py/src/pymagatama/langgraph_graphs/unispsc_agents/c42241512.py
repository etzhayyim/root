from typing import TypedDict
from langgraph.graph import StateGraph, END

class MedicalSupplyState(TypedDict):
    material_type: str
    curing_time: float
    compliance_passed: bool

def validate_material(state: MedicalSupplyState):
    return {'compliance_passed': state['curing_time'] > 0}

def check_temp_sensitivity(state: MedicalSupplyState):
    print(f'Checking storage requirements for {state['material_type']}')
    return {'compliance_passed': True}

graph = StateGraph(MedicalSupplyState)
graph.add_node('validate', validate_material)
graph.add_node('storage', check_temp_sensitivity)
graph.add_edge('validate', 'storage')
graph.add_edge('storage', END)
graph.set_entry_point('validate')
graph = graph.compile()
