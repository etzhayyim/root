from typing import TypedDict
from langgraph.graph import StateGraph, END

class SpeedSwitchState(TypedDict):
    spec_data: dict
    validation_status: bool
    error_log: list

def validate_specs(state: SpeedSwitchState):
    error = []
    if state['spec_data'].get('voltage', 0) <= 0:
        error.append('Invalid voltage')
    return {'validation_status': len(error) == 0, 'error_log': error}

graph = StateGraph(SpeedSwitchState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
