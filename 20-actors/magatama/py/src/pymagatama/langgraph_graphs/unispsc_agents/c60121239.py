from typing import TypedDict
from langgraph.graph import StateGraph, END

class PaintSupplyState(TypedDict):
    capacity_ml: int
    material: str
    is_leakproof: bool

def validate_specs(state: PaintSupplyState):
    if state['capacity_ml'] <= 0:
        raise ValueError('Capacity must be positive')
    return {'status': 'validated'}

def check_material(state: PaintSupplyState):
    allowed = ['HDPE', 'PET', 'Glass']
    if state['material'] not in allowed:
        print(f'Warning: Non-standard material {state[\"material\"]}')
    return {'material_check': 'passed'}

graph = StateGraph(PaintSupplyState)
graph.add_node('validate', validate_specs)
graph.add_node('check_material', check_material)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check_material')
graph.add_edge('check_material', END)
graph = graph.compile()