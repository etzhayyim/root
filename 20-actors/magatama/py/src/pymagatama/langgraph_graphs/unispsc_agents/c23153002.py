from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolSpec(TypedDict):
    material: str
    coating: str
    tolerance: float

def validate_tool_specs(state: ToolSpec):
    if state['tolerance'] < 0.001:
        return {'status': 'HighPrecision'}
    return {'status': 'Standard'}

def perform_export_check(state: ToolSpec):
    return {'export_cleared': True}

graph = StateGraph(ToolSpec)
graph.add_node('validate', validate_tool_specs)
graph.add_node('export', perform_export_check)
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph.set_entry_point('validate')
graph = graph.compile()