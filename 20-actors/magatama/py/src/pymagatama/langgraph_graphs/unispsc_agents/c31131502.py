from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    specs: dict
    approved: bool
    validation_log: List[str]

def validate_material(state: ForgingState):
    material = state['specs'].get('material_grade')
    is_valid = material in ['AISI 4140', 'AISI 4340']
    return {'validation_log': [f'Material check: {is_valid}'], 'approved': is_valid}

def validate_dimensions(state: ForgingState):
    dims = state['specs'].get('dimensions', {})
    is_valid = dims.get('tolerance', 0) < 0.05
    return {'validation_log': state['validation_log'] + [f'Dimension check: {is_valid}'], 'approved': is_valid}

graph = StateGraph(ForgingState)
graph.add_node('material_check', validate_material)
graph.add_node('dimension_check', validate_dimensions)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'dimension_check')
graph.add_edge('dimension_check', END)
graph = graph.compile()
