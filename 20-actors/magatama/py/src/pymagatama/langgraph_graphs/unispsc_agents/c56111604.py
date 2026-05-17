from typing import TypedDict
from langgraph.graph import StateGraph, END

class WorkSurfaceState(TypedDict):
    specs: dict
    approved: bool
    validation_log: list

def validate_specs(state: WorkSurfaceState):
    log = []
    is_valid = True
    if 'load_capacity' in state['specs'] and state['specs']['load_capacity'] < 50:
        log.append('Capacity too low')
        is_valid = False
    return {'approved': is_valid, 'validation_log': log}

graph = StateGraph(WorkSurfaceState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
compile_graph = graph.compile()