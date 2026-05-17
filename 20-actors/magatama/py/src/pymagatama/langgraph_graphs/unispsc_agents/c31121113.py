from typing import TypedDict
from langgraph.graph import StateGraph, END

class CopperDieState(TypedDict):
    spec_data: dict
    inspection_result: bool

def validate_materials(state: CopperDieState):
    content = state['spec_data']
    return {'inspection_result': 'CopperContent' in content and content['CopperContent'] >= 99.0}

def quality_check(state: CopperDieState):
    return {'inspection_result': state['inspection_result'] and 'TolerancePassed' in state['spec_data']}

graph = StateGraph(CopperDieState)
graph.add_node('material_validation', validate_materials)
graph.add_node('quality_assurance', quality_check)
graph.set_entry_point('material_validation')
graph.add_edge('material_validation', 'quality_assurance')
graph.add_edge('quality_assurance', END)
graph = graph.compile()