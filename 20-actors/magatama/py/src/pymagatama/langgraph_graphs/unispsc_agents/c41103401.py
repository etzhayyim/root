from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ScreenState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_specs(state: ScreenState):
    log = []
    compliant = True
    if state['specs'].get('ISO_class_rating', 0) > 8:
        log.append('ISO rating exceeds cleanroom threshold.')
        compliant = False
    return {'is_compliant': compliant, 'validation_log': log}

graph = StateGraph(ScreenState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()