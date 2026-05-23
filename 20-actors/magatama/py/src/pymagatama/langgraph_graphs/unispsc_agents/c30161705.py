from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class FlooringState(TypedDict):
    specs: dict
    approved: bool
    validation_log: List[str]

def validate_durability(state: FlooringState):
    thickness = state['specs'].get('thickness', 0)
    if thickness >= 3:
        state['validation_log'].append('Durability validated for high traffic.')
        state['approved'] = True
    else:
        state['validation_log'].append('Insufficient thickness for specified usage.')
        state['approved'] = False
    return state

graph = StateGraph(FlooringState)
graph.add_node('validate', validate_durability)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
