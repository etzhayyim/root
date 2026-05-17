from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PumpState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_pump_specs(state: PumpState):
    errors = []
    if state['specs'].get('efficiency', 0) < 70:
        errors.append('Low pump efficiency')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(PumpState)
graph.add_node('validate', validate_pump_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()