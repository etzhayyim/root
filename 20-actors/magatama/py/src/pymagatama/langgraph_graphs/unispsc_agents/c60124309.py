from typing import TypedDict
from langgraph.graph import StateGraph, END

class PotteryState(TypedDict):
    material: str
    dimensions: dict
    approved: bool

def validate_material(state: PotteryState):
    state['approved'] = state['material'] in ['MDF', 'Plaster', 'Plastic']
    return state

def check_dimensions(state: PotteryState):
    if state['approved'] and state['dimensions'].get('diameter_cm', 0) > 0:
        state['approved'] = True
    else:
        state['approved'] = False
    return state

graph = StateGraph(PotteryState)
graph.add_node('validate', validate_material)
graph.add_node('specs', check_dimensions)
graph.set_entry_point('validate')
graph.add_edge('validate', 'specs')
graph.add_edge('specs', END)
graph = graph.compile()
