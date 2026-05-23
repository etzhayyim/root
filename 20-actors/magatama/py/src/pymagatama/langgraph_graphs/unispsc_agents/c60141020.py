from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BoomerangState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: BoomerangState) -> BoomerangState:
    required = ['material', 'weight']
    passed = all(k in state['specs'] for k in required)
    state['validation_passed'] = passed
    state['compliance_report'] = 'Valid' if passed else 'Missing specifications'
    return state

workflow = StateGraph(BoomerangState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
