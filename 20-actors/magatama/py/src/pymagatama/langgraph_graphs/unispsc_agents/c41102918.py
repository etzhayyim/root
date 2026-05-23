from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LabSupplyState(TypedDict):
    item_name: str
    specs: List[str]
    approved: bool

def validate_specs(state: LabSupplyState):
    required = ['Material composition', 'Anti-static rating']
    state['approved'] = all(item in state['specs'] for item in required)
    return state

graph = StateGraph(LabSupplyState)
graph.add_node('validator', validate_specs)
graph.set_entry_point('validator')
graph.add_edge('validator', END)
graph = graph.compile()
