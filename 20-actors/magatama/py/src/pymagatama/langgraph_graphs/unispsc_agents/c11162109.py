from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AlloyState(TypedDict):
    material_id: str
    purity_level: float
    inspection_passed: bool
    log: List[str]

def validate_material(state: AlloyState):
    passed = state['purity_level'] >= 99.9
    return {'inspection_passed': passed, 'log': [f'Material {state['material_id']} purity check: {passed}']}

def process_alloy(state: AlloyState):
    if state['inspection_passed']:
        return {'log': state['log'] + ['Alloy cleared for production.']}
    else:
        return {'log': state['log'] + ['Alloy rejected due to purity failure.']}

graph = StateGraph(AlloyState)
graph.add_node('validate', validate_material)
graph.add_node('process', process_alloy)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
compile_graph = graph.compile()