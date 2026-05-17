from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DentalAlloyState(TypedDict):
    alloy_code: str
    spec_check: bool
    compliance_docs: List[str]

def validate_alloy_specs(state: DentalAlloyState):
    # Business logic for dental brazing alloy validation
    is_compliant = all(doc in ['iso_cert', 'msds'] for doc in state['compliance_docs'])
    print(f'Validating alloy: {state['alloy_code']}')
    return {'spec_check': is_compliant}

workflow = StateGraph(DentalAlloyState)
workflow.add_node('validate', validate_alloy_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()