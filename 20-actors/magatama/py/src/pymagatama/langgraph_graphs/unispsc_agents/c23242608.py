from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolPresetterState(TypedDict):
    specs: dict
    validation_status: str

def validate_specs(state: ToolPresetterState):
    if state['specs'].get('repeatability', 0.005) <= 0.01:
        return {'validation_status': 'passed'}
    return {'validation_status': 'manual_review'}

graph = StateGraph(ToolPresetterState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
