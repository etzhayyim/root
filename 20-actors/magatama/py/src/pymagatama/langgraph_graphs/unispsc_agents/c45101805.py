from typing import TypedDict
from langgraph.graph import StateGraph, END

class JoggerState(TypedDict):
    model_number: str
    spec_compliant: bool
    validation_log: list

def validate_specs(state: JoggerState):
    # Business logic for validating book jogger procurement specs
    is_valid = True if state['model_number'] else False
    return {'spec_compliant': is_valid, 'validation_log': ['Physical spec check complete']}

def approve_order(state: JoggerState):
    return {'validation_log': state['validation_log'] + ['Order approved for procurement']}

graph = StateGraph(JoggerState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approve_order)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()