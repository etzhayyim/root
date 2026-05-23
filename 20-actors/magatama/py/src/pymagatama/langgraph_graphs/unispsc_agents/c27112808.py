import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END

class ColletState(TypedDict):
    spec_data: dict
    validation_errors: Annotated[list, operator.add]
    is_compliant: bool

def validate_runout(state: ColletState):
    errors = []
    if state['spec_data'].get('run_out', 0.005) > 0.01:
        errors.append('Run-out tolerance exceeds precision limit')
    return {'validation_errors': errors}

def check_compliance(state: ColletState):
    compliant = len(state['validation_errors']) == 0
    return {'is_compliant': compliant}

graph = StateGraph(ColletState)
graph.add_node('validate', validate_runout)
graph.add_node('check', check_compliance)
graph.add_edge('validate', 'check')
graph.add_edge('check', END)
graph.set_entry_point('validate')
graph = graph.compile()
