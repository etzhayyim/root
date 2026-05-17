from typing import TypedDict
from langgraph.graph import StateGraph, END

class ArtProcurementState(TypedDict):
    painting_data: dict
    validation_passed: bool
    insurance_check: bool

def validate_provenance(state: ArtProcurementState):
    provenance = state['painting_data'].get('provenance', [])
    return {'validation_passed': len(provenance) > 0}

def verify_insurance(state: ArtProcurementState):
    value = state['painting_data'].get('appraisal_value', 0)
    return {'insurance_check': value > 0}

graph = StateGraph(ArtProcurementState)
graph.add_node('validate', validate_provenance)
graph.add_node('insurance', verify_insurance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'insurance')
graph.add_edge('insurance', END)
app = graph.compile()