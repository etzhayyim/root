from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class FurnitureState(TypedDict):
    spec_data: dict
    validation_log: Annotated[list, operator.add]
    is_compliant: bool

def validate_dimensions(state: FurnitureState):
    dims = state['spec_data'].get('dimensions', {})
    compliant = all(d > 0 for d in dims.values())
    return {'validation_log': ['Dimensions validated'], 'is_compliant': compliant}

def check_material_safety(state: FurnitureState):
    material = state['spec_data'].get('material', 'unknown')
    status = 'Safety compliant' if material != 'toxic' else 'Safety failed'
    return {'validation_log': [status]}

graph = StateGraph(FurnitureState)
graph.add_node('validate_dims', validate_dimensions)
graph.add_node('check_safety', check_material_safety)
graph.set_entry_point('validate_dims')
graph.add_edge('validate_dims', 'check_safety')
graph.add_edge('check_safety', END)
graph = graph.compile()
