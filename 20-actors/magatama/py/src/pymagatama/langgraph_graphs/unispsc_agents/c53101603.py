from langgraph.graph import StateGraph, END
from typing import TypedDict, List
class GarmentState(TypedDict):
    item_id: str
    specs: dict
    validation_errors: List[str]
    is_approved: bool
def validate_material(state: GarmentState):
    errors = []
    if 'material' not in state['specs']: errors.append('Missing material info')
    return {'validation_errors': errors}
def finalize_procurement(state: GarmentState):
    return {'is_approved': len(state['validation_errors']) == 0}
graph = StateGraph(GarmentState)
graph.add_node('validate', validate_material)
graph.add_node('finish', finalize_procurement)
graph.add_edge('validate', 'finish')
graph.add_edge('finish', END)
graph.set_entry_point('validate')
