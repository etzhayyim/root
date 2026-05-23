from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EquipmentState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_log: List[str]

def validate_food_safety(state: EquipmentState):
    check = state['spec_data'].get('food_safety_cert', False)
    return {'is_compliant': check, 'validation_log': ['Food safety certification verified' if check else 'Certification missing']}

def validate_specs(state: EquipmentState):
    log = ['Specs checked']
    return {'validation_log': log}

graph = StateGraph(EquipmentState)
graph.add_node('safety_check', validate_food_safety)
graph.add_node('spec_check', validate_specs)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'spec_check')
graph.add_edge('spec_check', END)
graph = graph.compile()
