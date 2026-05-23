from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_insulation(state: ToolState):
    state['is_compliant'] = state['spec_data'].get('insulation_kv', 0) >= 1.0
    return state

def validate_hardness(state: ToolState):
    state['is_compliant'] = state['is_compliant'] and state['spec_data'].get('hrc', 0) >= 58
    return state

graph = StateGraph(ToolState)
graph.add_node('insulation', validate_insulation)
graph.add_node('hardness', validate_hardness)
graph.set_entry_point('insulation')
graph.add_edge('insulation', 'hardness')
graph.add_edge('hardness', END)
compiled_graph = graph.compile()
