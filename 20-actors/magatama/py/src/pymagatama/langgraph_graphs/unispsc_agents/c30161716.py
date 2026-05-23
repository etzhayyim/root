from typing import TypedDict
from langgraph.graph import StateGraph, END

class TileSpacerState(TypedDict):
    thickness: float
    material: str
    is_reusable: bool
    validation_passed: bool

def validate_spacer_specs(state: TileSpacerState):
    state['validation_passed'] = state['thickness'] > 0 and isinstance(state['material'], str)
    return state

def packing_logic(state: TileSpacerState):
    print(f'Processing spacer order for {state['thickness']}mm size')
    return state

graph = StateGraph(TileSpacerState)
graph.add_node('validate', validate_spacer_specs)
graph.add_node('pack', packing_logic)
graph.add_edge('validate', 'pack')
graph.add_edge('pack', END)
graph.set_entry_point('validate')
graph = graph.compile()
