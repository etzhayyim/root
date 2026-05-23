from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class BrickState(TypedDict):
    specs: dict
    validation_log: List[str]
    is_approved: bool

def validate_specs(state: BrickState):
    required = ['compressive_strength_mpa', 'water_absorption_rate']
    logs = []
    for field in required:
        if field not in state['specs']:
            logs.append(f'Missing spec: {field}')
    return {'validation_log': logs, 'is_approved': len(logs) == 0}

graph = StateGraph(BrickState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
