from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MosaicProcessState(TypedDict):
    tool_type: str
    material_compatibility: List[str]
    needs_inspection: bool

def validate_tools(state: MosaicProcessState):
    state['needs_inspection'] = state['tool_type'] in ['cutter', 'nipper']
    return state

def route_by_inspection(state: MosaicProcessState):
    return 'inspection' if state['needs_inspection'] else END

graph = StateGraph(MosaicProcessState)
graph.add_node('validate', validate_tools)
graph.add_node('inspection', lambda x: x)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_inspection)
graph.add_edge('inspection', END)

app = graph.compile()
