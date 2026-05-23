from typing import TypedDict
from langgraph.graph import StateGraph, END

class BatonState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_baton_specs(state: BatonState):
    specs = state['spec_data']
    passed = all(key in specs for key in ['length', 'weight', 'material'])
    print(f'Validating baton specs: {specs}')
    return {'validation_passed': passed}

workflow = StateGraph(BatonState)
workflow.add_node('validation', validate_baton_specs)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()
