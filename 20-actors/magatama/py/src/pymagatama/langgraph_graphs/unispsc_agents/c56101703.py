from typing import TypedDict
from langgraph.graph import StateGraph, END

class DeskProcureState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_compliant: bool

def validate_desk_specs(state: DeskProcureState):
    errors = []
    if state['spec_data'].get('weight_capacity', 0) < 50:
        errors.append('Weight capacity below safety threshold')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def finalizer(state: DeskProcureState):
    print(f'Compliance status: {state['is_compliant']}')
    return {}

graph = StateGraph(DeskProcureState)
graph.add_node('validate', validate_desk_specs)
graph.add_node('finalize', finalizer)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()
