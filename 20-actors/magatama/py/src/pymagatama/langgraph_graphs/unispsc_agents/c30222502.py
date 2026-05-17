from typing import TypedDict
from langgraph.graph import StateGraph, END

class FlatSteelState(TypedDict):
    material_grade: str
    thickness: float
    width: float
    certification_verified: bool

def validate_specs(state: FlatSteelState):
    valid = state.get('material_grade') is not None and state.get('thickness') > 0
    return {'certification_verified': valid}

def route(state: FlatSteelState):
    return 'process' if state['certification_verified'] else END

def process_order(state: FlatSteelState):
    print(f'Processing flat steel order for grade: {state['material_grade']}')
    return {'certification_verified': True}

graph = StateGraph(FlatSteelState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_order)
graph.add_edge('validate', 'process')
graph.add_conditional_edges('validate', route, {'process': 'process', '__end__': END})
graph.set_entry_point('validate')
graph.set_finish_point('process')
graph = graph.compile()