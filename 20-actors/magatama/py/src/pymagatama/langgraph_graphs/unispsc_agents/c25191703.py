from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TireMachineState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: TireMachineState):
    errors = []
    if 'max_tire_diameter' not in state['specs']: errors.append('Missing diameter')
    return {'validation_errors': errors}

def check_compliance(state: TireMachineState):
    is_ok = len(state['validation_errors']) == 0
    return {'approved': is_ok}

graph = StateGraph(TireMachineState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
