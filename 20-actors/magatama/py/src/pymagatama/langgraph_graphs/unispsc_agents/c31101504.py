from typing import TypedDict
from langgraph.graph import StateGraph, END
class DieCastState(TypedDict):
    material_mix: str
    geometry_check: bool
    compliance_passed: bool
def validate_materials(state: DieCastState):
    state['compliance_passed'] = 'Al' in state['material_mix'] or 'Mg' in state['material_mix']
    return state
def run_inspection(state: DieCastState):
    print('Running non-destructive porosity inspection...')
    return {'geometry_check': True}
graph = StateGraph(DieCastState)
graph.add_node('validation', validate_materials)
graph.add_node('inspection', run_inspection)
graph.set_entry_point('validation')
graph.add_edge('validation', 'inspection')
graph.add_edge('inspection', END)
graph = graph.compile()