from typing import TypedDict
from langgraph.graph import StateGraph, END

class MuffinPanState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_material(state: MuffinPanState):
    material = state['spec_data'].get('material')
    state['validation_passed'] = bool(material and material in ['steel', 'silicone', 'aluminum'])
    print('Validating materials for bakeware...')
    return 'validate_safety'

def validate_safety(state: MuffinPanState):
    has_cert = state['spec_data'].get('food_safety_cert', False)
    state['validation_passed'] = state['validation_passed'] and has_cert
    return END

graph = StateGraph(MuffinPanState)
graph.add_node('validate_material', validate_material)
graph.add_node('validate_safety', validate_safety)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'validate_safety')
# graph = graph.compile()