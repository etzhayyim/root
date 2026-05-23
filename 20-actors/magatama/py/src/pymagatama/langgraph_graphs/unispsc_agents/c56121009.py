from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcureState(TypedDict):
    table_specs: dict
    approved: bool
    validation_log: list

def validate_specs(state: ProcureState):
    log = []
    if state['table_specs'].get('angle', 0) < 15:
        log.append('Angle too low for ergonomic needs')
    return {'validation_log': log}

def approval_check(state: ProcureState):
    return {'approved': len(state['validation_log']) == 0}

graph = StateGraph(ProcureState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_check)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
