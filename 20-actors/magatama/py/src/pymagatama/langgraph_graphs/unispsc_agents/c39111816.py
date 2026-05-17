from typing import TypedDict
from langgraph.graph import StateGraph, END
class LensState(TypedDict):
    spec_data: dict
    validated: bool
    error: str
def validate_optical_specs(state: LensState):
    specs = state['spec_data']
    if specs.get('light_transmittance', 0) < 0.90:
        return {'validated': False, 'error': 'Low transmittance'}
    return {'validated': True}
def finalize_procurement(state: LensState):
    print('Proceeding to procurement workflow')
    return {'validated': True}
graph = StateGraph(LensState)
graph.add_node('validate', validate_optical_specs)
graph.add_node('procurement', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'procurement')
graph.add_edge('procurement', END)
graph = graph.compile()