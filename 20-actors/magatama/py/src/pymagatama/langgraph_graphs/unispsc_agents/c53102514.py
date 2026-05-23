from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    specs: dict
    approved: bool

def validate_material(state: ProcurementState):
    material = state['specs'].get('material_composition', '')
    is_valid = material in ['PVC', 'Vinyl', 'Anti-static Plastic']
    return {'approved': is_valid}

def finalize_procurement(state: ProcurementState):
    print(f'Finalizing specs for {state['item_name']}')
    return {'approved': True}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_material)
graph.add_node('finalize', finalize_procurement)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
