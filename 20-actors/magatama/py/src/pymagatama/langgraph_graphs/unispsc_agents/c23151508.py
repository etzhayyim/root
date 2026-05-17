from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END

class ActuatorSpecState(TypedDict):
    spec_data: dict
    is_validated: bool
    validation_log: list

def validate_specs(state: ActuatorSpecState):
    fields = ['force', 'stroke', 'ip_rating']
    log = []
    for field in fields:
        if field not in state['spec_data']:
            log.append(f'Missing field: {field}')
    return {'is_validated': len(log) == 0, 'validation_log': log}

graph = StateGraph(ActuatorSpecState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()