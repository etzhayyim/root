from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LightingState(TypedDict):
    specs: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: LightingState):
    errors = []
    if state['specs'].get('dmx_protocol') != 'DMX512':
        errors.append('Invalid DMX protocol')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def safety_check(state: LightingState):
    if state['specs'].get('safety_cert') is None:
        return {'validation_passed': False, 'errors': ['Missing safety certification']}
    return {'validation_passed': True}

workflow = StateGraph(LightingState)
workflow.add_node('validate', validate_specs)
workflow.add_node('safety', safety_check)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'safety')
workflow.add_edge('safety', END)
graph = workflow.compile()
