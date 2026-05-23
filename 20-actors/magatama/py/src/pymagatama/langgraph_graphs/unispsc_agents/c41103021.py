from typing import TypedDict
from langgraph.graph import StateGraph, END

class FreezerState(TypedDict):
    temp_setting: float
    validation_status: bool
    error_log: list

def validate_temp(state: FreezerState):
    is_valid = state['temp_setting'] <= -80.0
    return {'validation_status': is_valid}

def audit_log(state: FreezerState):
    if not state.get('validation_status'):
        state['error_log'].append('Critical temperature failure')
    return state

graph = StateGraph(FreezerState)
graph.add_node('validate', validate_temp)
graph.add_node('audit', audit_log)
graph.set_entry_point('validate')
graph.add_edge('validate', 'audit')
graph.add_edge('audit', END)
graph = graph.compile()
