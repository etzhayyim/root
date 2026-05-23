from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalChairState(TypedDict):
    spec_data: dict
    validation_result: bool
    compliance_score: int

def validate_ergonomics(state: DentalChairState):
    # Business logic for dental stool compliance
    is_valid = state['spec_data'].get('ergonomic_standard') == 'ISO-9241'
    return {'validation_result': is_valid}

def assess_compliance(state: DentalChairState):
    return {'compliance_score': 100 if state['validation_result'] else 0}

graph = StateGraph(DentalChairState)
graph.add_node('validate', validate_ergonomics)
graph.add_node('assess', assess_compliance)
graph.add_edge('validate', 'assess')
graph.add_edge('assess', END)
graph.set_entry_point('validate')
graph = graph.compile()
