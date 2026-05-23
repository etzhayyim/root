from typing import TypedDict
from langgraph.graph import StateGraph, END

class StickerState(TypedDict):
    specs: dict
    validated: bool

def validate_specs(state: StickerState):
    required = ['printer_type', 'finish']
    state['validated'] = all(k in state['specs'] for k in required)
    return state

graph = StateGraph(StickerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()
