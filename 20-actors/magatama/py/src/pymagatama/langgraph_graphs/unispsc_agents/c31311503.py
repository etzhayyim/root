from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PipeAssemblyState(TypedDict):
    specs: dict
    validation_results: List[str]
    is_compliant: bool

def validate_material(state: PipeAssemblyState):
    is_alloy_x = state['specs'].get('alloy_type') == 'Hastelloy X'
    return {'validation_results': ['Material check passed'] if is_alloy_x else ['Invalid Alloy Error']}

def conduct_nd_testing(state: PipeAssemblyState):
    is_passed = state['specs'].get('rt_score', 0) > 95
    return {'validation_results': state['validation_results'] + ['NDT Passed'] if is_passed else ['NDT Failed']}

graph = StateGraph(PipeAssemblyState)
graph.add_node('validate_material', validate_material)
graph.add_node('conduct_ndt', conduct_nd_testing)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'conduct_ndt')
graph.add_edge('conduct_ndt', END)
graph = graph.compile()
