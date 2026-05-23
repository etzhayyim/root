from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DentalSpecState(TypedDict):
    material_compliance: bool
    tensile_tests: List[float]
    approval_status: str

def validate_material(state: DentalSpecState):
    return {'material_compliance': state.get('material_compliance', False)}

def check_quality(state: DentalSpecState):
    avg_tensile = sum(state['tensile_tests']) / len(state['tensile_tests']) if state['tensile_tests'] else 0
    return {'approval_status': 'APPROVED' if avg_tensile > 5.0 else 'REJECTED'}

graph = StateGraph(DentalSpecState)
graph.add_node('validate', validate_material)
graph.add_node('quality_check', check_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', 'quality_check')
graph.add_edge('quality_check', END)
compiled_graph = graph.compile()
