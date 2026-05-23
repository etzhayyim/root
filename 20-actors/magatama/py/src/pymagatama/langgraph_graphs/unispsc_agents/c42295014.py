from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EndoscopeCaseState(TypedDict):
    case_id: str
    material_certified: bool
    sterilization_validated: bool
    passed_inspection: bool

def validate_material(state: EndoscopeCaseState):
    print(f'Validating material specifications for {state["case_id"]}')
    return {'material_certified': True}

def check_sterilization_compliance(state: EndoscopeCaseState):
    print('Checking sterilization cycle compatibility...')
    return {'sterilization_validated': True}

def final_quality_gate(state: EndoscopeCaseState):
    passed = state['material_certified'] and state['sterilization_validated']
    return {'passed_inspection': passed}

graph = StateGraph(EndoscopeCaseState)
graph.add_node('validate_material', validate_material)
graph.add_node('sterilization_check', check_sterilization_compliance)
graph.add_node('final_gate', final_quality_gate)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'sterilization_check')
graph.add_edge('sterilization_check', 'final_gate')
graph.add_edge('final_gate', END)
