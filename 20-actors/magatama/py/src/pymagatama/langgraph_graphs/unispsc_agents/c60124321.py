from typing import TypedDict
from langgraph.graph import StateGraph, END

class ModelingMaterialState(TypedDict):
    material_type: str
    curing_temp: int
    safety_compliant: bool

def validate_material(state: ModelingMaterialState):
    if state['curing_temp'] > 150:
        return {'safety_compliant': False}
    return {'safety_compliant': True}

def finalize_order(state: ModelingMaterialState):
    return {'status': 'READY_FOR_PROCUREMENT'}

graph = StateGraph(ModelingMaterialState)
graph.add_node('validate', validate_material)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()
