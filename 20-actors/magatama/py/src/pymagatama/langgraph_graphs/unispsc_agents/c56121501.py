from typing import TypedDict
from langgraph.graph import StateGraph, END

class ActivityTableState(TypedDict):
    specs: dict
    approved: bool
    validation_log: list

def validate_specs(state: ActivityTableState):
    log = []
    if state['specs'].get('load_capacity', 0) < 50:
        log.append('Load capacity below safety threshold')
    return {'validation_log': log, 'approved': len(log) == 0}

graph = StateGraph(ActivityTableState)
graph.add_node('validator', validate_specs)
graph.set_entry_point('validator')
graph.add_edge('validator', END)
graph = graph.compile()
