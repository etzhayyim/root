from typing import TypedDict
from langgraph.graph import StateGraph, END

class CTState(TypedDict):
    power_rating: float
    compliance_docs: list
    validation_status: str

def validate_specs(state: CTState):
    if state['power_rating'] < 50:
        return {'validation_status': 'Underpowered'}
    return {'validation_status': 'Verified'}

def check_compliance(state: CTState):
    required = ['ISO_13485', 'IEC_60601']
    if all(doc in state['compliance_docs'] for doc in required):
        return {'validation_status': 'Compliant'}
    return {'validation_status': 'Non-Compliant'}

graph = StateGraph(CTState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
