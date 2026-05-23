from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class GeometrySpecState(TypedDict):
    material: str
    tolerance: float
    is_compliant: bool
    validation_log: List[str]

def validate_material(state: GeometrySpecState):
    state['validation_log'].append(f'Checking material: {state['material']}')
    return {'is_compliant': state['material'] in ['polycarbonate', 'aluminum']}

def validate_tolerance(state: GeometrySpecState):
    state['validation_log'].append(f'Checking tolerance: {state['tolerance']}')
    return {'is_compliant': state['tolerance'] <= 0.05}

graph = StateGraph(GeometrySpecState)
graph.add_node('material_check', validate_material)
graph.add_node('tolerance_check', validate_tolerance)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'tolerance_check')
graph.add_edge('tolerance_check', END)
app = graph.compile()
