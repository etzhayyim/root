from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MaterialState(TypedDict):
    material_id: str
    purity_level: float
    inspection_passed: bool
    log: List[str]

def validate_material(state: MaterialState):
    passed = state.get('purity_level', 0) >= 99.9
    return {'inspection_passed': passed, 'log': state['log'] + ['Material purity validation completed.']}

def route_by_purity(state: MaterialState):
    return 'validate' if not state.get('inspection_passed') else END

def finalize_procurement(state: MaterialState):
    return {'log': state['log'] + ['Procurement finalized successfully.']}

graph = StateGraph(MaterialState)
graph.add_node('validate', validate_material)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_purity)
graph.add_edge('finalize', END)

compiled_graph = graph.compile()
