from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WallTreatmentState(TypedDict):
    material_type: str
    spec_data: dict
    approved: bool

def validate_materials(state: WallTreatmentState):
    # Logic to check for fire safety and VOC compliance
    is_compliant = 'fire_resistance_class' in state['spec_data']
    return {'approved': is_compliant}

def process_procurement(state: WallTreatmentState):
    print(f'Processing procurement for {state['material_type']}')
    return {'approved': True}

graph = StateGraph(WallTreatmentState)
graph.add_node('validate', validate_materials)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()