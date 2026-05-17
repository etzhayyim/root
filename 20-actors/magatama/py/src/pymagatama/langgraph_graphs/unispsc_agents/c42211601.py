from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BathBoardState(TypedDict):
    product_specs: dict
    compliance_checks: List[str]
    is_approved: bool

def validate_load_capacity(state: BathBoardState):
    load = state['product_specs'].get('load_capacity_kg', 0)
    state['compliance_checks'].append(f'Load capacity {load}kg validated.')
    return {'is_approved': load >= 120}

def check_materials(state: BathBoardState):
    material = state['product_specs'].get('material', '')
    is_safe = material in ['polypropylene', 'stainless_steel']
    state['compliance_checks'].append(f'Material safety: {is_safe}')
    return {'is_approved': is_safe}

graph = StateGraph(BathBoardState)
graph.add_node('validate_load', validate_load_capacity)
graph.add_node('check_materials', check_materials)
graph.set_entry_point('validate_load')
graph.add_edge('validate_load', 'check_materials')
graph.add_edge('check_materials', END)
graph = graph.compile()