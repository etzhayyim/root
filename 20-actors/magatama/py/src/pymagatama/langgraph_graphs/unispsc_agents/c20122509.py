from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ServoState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: ServoState):
    errors = []
    if not state['spec_data'].get('safety_certification_iso'):
        errors.append('Missing ISO safety certification')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def compile_servo_graph():
    workflow = StateGraph(ServoState)
    workflow.add_node('validate', validate_specs)
    workflow.set_entry_point('validate')
    workflow.add_edge('validate', END)
    return workflow.compile()

graph = compile_servo_graph()
