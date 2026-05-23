from langgraph.graph import StateGraph, END
from typing import TypedDict, List
class ZincState(TypedDict):
    spec_data: dict
    validation_results: List[str]
    approved: bool
def validate_dimensions(state: ZincState):
    errs = []
    if state['spec_data'].get('tolerance', 0.05) > 0.1:
         errs.append('Tolerance out of range')
    return {'validation_results': errs, 'approved': len(errs) == 0}
def check_material(state: ZincState):
    is_zinc = state['spec_data'].get('material') == 'Zinc-Alloy-Standard'
    return {'validation_results': ['Invalid Material'] if not is_zinc else []}
graph = StateGraph(ZincState)
graph.add_node('validate', validate_dimensions)
graph.add_node('material_check', check_material)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'validate')
graph.add_edge('validate', END)
graph = graph.compile()
