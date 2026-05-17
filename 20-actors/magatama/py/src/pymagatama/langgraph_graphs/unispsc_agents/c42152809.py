from typing import TypedDict, List
from langgraph.graph import StateGraph, END
class DentalToolState(TypedDict):
    tool_id: str
    material_spec: str
    is_compliant: bool
    history: List[str]
def validate_material(state: DentalToolState):
    compliant = state['material_spec'] == 'Medical Grade Stainless Steel'
    return {'is_compliant': compliant, 'history': state.get('history', []) + ['material_check']}
def finalize_approval(state: DentalToolState):
    return {'history': state.get('history', []) + ['approval_flag']}
graph = StateGraph(DentalToolState)
graph.add_node('validate', validate_material)
graph.add_node('approve', finalize_approval)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()