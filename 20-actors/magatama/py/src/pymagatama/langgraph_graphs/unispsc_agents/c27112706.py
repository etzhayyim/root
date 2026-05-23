from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolSpec(TypedDict):
    voltage: int
    width: float
    speed: int
    safety_compliant: bool

def validate_tool_specs(state: ToolSpec):
    if state['voltage'] not in [110, 220, 240]:
        raise ValueError('Unsupported voltage')
    return {'status': 'validated'}

def process_procurement(state: ToolSpec):
    return {'result': 'Procurement criteria met for power plane.'}

graph = StateGraph(ToolSpec)
graph.add_node('validate', validate_tool_specs)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()
