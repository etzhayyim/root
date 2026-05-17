from typing import TypedDict
from langgraph.graph import StateGraph, END

class DisplayBoardState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: DisplayBoardState):
    required = ['board_material', 'dimensions']
    all_present = all(k in state['specs'] for k in required)
    return {'approved': all_present}

graph = StateGraph(DisplayBoardState)
graph.add_node('validation', validate_specs)
graph.set_entry_point('validation')
graph.add_edge('validation', END)

graph = graph.compile()