from typing import TypedDict
from langgraph.graph import StateGraph, END

class PrintingElementState(TypedDict):
    model_number: str
    compatibility_verified: bool
    spec_sheet_uploaded: bool

def verify_compatibility(state: PrintingElementState):
    state['compatibility_verified'] = state['model_number'] is not None
    return state

def check_docs(state: PrintingElementState):
    state['spec_sheet_uploaded'] = True
    return state

graph = StateGraph(PrintingElementState)
graph.add_node('verify', verify_compatibility)
graph.add_node('docs', check_docs)
graph.set_entry_point('verify')
graph.add_edge('verify', 'docs')
graph.add_edge('docs', END)
graph = graph.compile()