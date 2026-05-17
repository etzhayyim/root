from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BaitState(TypedDict):
    product_specs: dict
    validation_passed: bool
    compliance_tags: List[str]

def validate_material(state: BaitState):
    content = state['product_specs'].get('content', '')
    passed = 'toxic' not in content.lower()
    return {'validation_passed': passed}

def check_biodegradability(state: BaitState):
    tags = state.get('compliance_tags', [])
    if state['product_specs'].get('biodegradable', False):
        tags.append('environmental_safe')
    return {'compliance_tags': tags}

graph = StateGraph(BaitState)
graph.add_node('material_check', validate_material)
graph.add_node('eco_check', check_biodegradability)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'eco_check')
graph.add_edge('eco_check', END)
graph = graph.compile()