from typing import TypedDict
from langgraph.graph import StateGraph, END

class StickerBookState(TypedDict):
    spec_content: str
    safety_check_passed: bool

def validate_materials(state: StickerBookState):
    # Simulated validation of child-safety standards for adhesives
    return {'safety_check_passed': 'non-toxic' in state['spec_content']}

def finalize_order(state: StickerBookState):
    return {'spec_content': 'Validated: ' + state['spec_content']}

graph = StateGraph(StickerBookState)
graph.add_node('validate', validate_materials)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
