from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class MineralState(TypedDict):
    material_id: str
    purity_level: float
    compliance_cleared: bool
    history: Annotated[list, add_messages]

def validate_purity(state: MineralState):
    is_pure = state['purity_level'] >= 99.5
    return {'compliance_cleared': is_pure, 'history': [f'Purity check: {is_pure}']}

def check_sanctions(state: MineralState):
    return {'compliance_cleared': True, 'history': [f'Sanctions check passed for {state['material_id']}']}

def route_material(state: MineralState):
    if state['compliance_cleared']:
        return 'final'
    return 'flag'

graph = StateGraph(MineralState)
graph.add_node('validate', validate_purity)
graph.add_node('sanctions', check_sanctions)
graph.set_entry_point('validate')
graph.add_edge('validate', 'sanctions')
graph.add_conditional_edges('sanctions', route_material, {'final': END, 'flag': END})
graph = graph.compile()