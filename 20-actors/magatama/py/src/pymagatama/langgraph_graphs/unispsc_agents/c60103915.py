from typing import TypedDict
from langgraph.graph import StateGraph, END

class DissectionKitState(TypedDict):
    kit_id: str
    contents: list
    is_verified: bool

def validate_tools(state: DissectionKitState):
    state['is_verified'] = all(['scalpel' in state['contents'], 'forceps' in state['contents']])
    return state

graph = StateGraph(DissectionKitState)
graph.add_node('validate', validate_tools)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()