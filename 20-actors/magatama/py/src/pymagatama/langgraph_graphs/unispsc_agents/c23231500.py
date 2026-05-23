from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolSpecState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_tool_specs(state: ToolSpecState):
    required = ['material', 'tolerance', 'coating']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

def route_to_procurement(state: ToolSpecState):
    return 'procurement_step' if state['validation_passed'] else 'revise_specs'

graph = StateGraph(ToolSpecState)
graph.add_node('validation', validate_tool_specs)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
compile_graph = graph.compile()
