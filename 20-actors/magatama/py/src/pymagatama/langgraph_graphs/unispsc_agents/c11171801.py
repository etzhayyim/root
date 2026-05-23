from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    commodity_code: str
    purity: float
    particle_data: dict
    approved: bool
    logs: List[str]

def validate_quality(state: MineralState) -> MineralState:
    is_pure = state['purity'] >= 99.5
    state['approved'] = is_pure
    state['logs'].append(f'Quality validation: {is_pure}')
    return state

def check_hazards(state: MineralState) -> MineralState:
    state['logs'].append('Hazards checked')
    return state

graph = StateGraph(MineralState)
graph.add_node('validate', validate_quality)
graph.add_node('hazards', check_hazards)
graph.set_entry_point('validate')
graph.add_edge('validate', 'hazards')
graph.add_edge('hazards', END)

compiled_graph = graph.compile()
