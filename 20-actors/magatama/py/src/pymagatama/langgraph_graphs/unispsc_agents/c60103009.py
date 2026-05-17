from typing import TypedDict
from langgraph.graph import StateGraph, END

class TileState(TypedDict):
    material: str
    dimensions: dict
    is_compliant: bool

def validate_specs(state: TileState):
    state['is_compliant'] = state['material'] in ['plastic', 'wood'] and 'length' in state['dimensions']
    return state

def quality_check(state: TileState):
    print(f'Checking quality for material: {state['material']}')
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(TileState)
graph.add_node('validate', validate_specs)
graph.add_node('quality', quality_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'quality')
graph.add_edge('quality', END)
app = graph.compile()