from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class GeometryResourceState(TypedDict):
    material_items: List[dict]
    validation_logs: List[str]
    approved: bool

def validate_resource(state: GeometryResourceState):
    logs = []
    for item in state['material_items']:
        if 'educational_standard' not in item:
            logs.append(f'Missing standards for {item.get('name', 'unknown')}')
    return {'validation_logs': logs, 'approved': len(logs) == 0}

graph = StateGraph(GeometryResourceState)
graph.add_node('validate', validate_resource)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()