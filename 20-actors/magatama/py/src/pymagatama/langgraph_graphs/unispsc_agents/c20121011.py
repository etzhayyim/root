from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    spec: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_load_specs(state: BearingState) -> BearingState:
    spec = state['spec']
    if spec.get('load_rating', 0) > 0:
        return {'validation_log': ['Load rating verified'], 'is_compliant': True}
    return {'validation_log': ['Load rating missing'], 'is_compliant': False}

def check_iso_compliance(state: BearingState) -> BearingState:
    if state.get('spec', {}).get('iso_standard_compliance', False):
        return {'validation_log': ['ISO standard verified'], 'is_compliant': True}
    return {'validation_log': ['ISO standard failed'], 'is_compliant': False}

workflow = StateGraph(BearingState)
workflow.add_node('validate_load', validate_load_specs)
workflow.add_node('check_iso', check_iso_compliance)
workflow.set_entry_point('validate_load')
workflow.add_edge('validate_load', 'check_iso')
workflow.add_edge('check_iso', END)
graph = workflow.compile()
