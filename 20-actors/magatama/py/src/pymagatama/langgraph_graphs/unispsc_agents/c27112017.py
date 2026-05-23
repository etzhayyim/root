from typing import TypedDict
from langgraph.graph import StateGraph, END

class DiggingBarState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_log: list

def validate_spec(state: DiggingBarState):
    log = []
    required = ['Material Grade', 'Overall Length', 'Tip Hardness (HRC)']
    is_valid = all(key in state['spec_data'] for key in required)
    if not is_valid:
        log.append('Missing mandatory specifications')
    return {'is_compliant': is_valid, 'validation_log': log}

graph = StateGraph(DiggingBarState)
graph.add_node('validate', validate_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
