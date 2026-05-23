from typing import TypedDict
from langgraph.graph import StateGraph, END

class MicrobiocideState(TypedDict):
    chemical_composition: str
    toxicity_level: float
    compliance_docs: list
    validation_status: bool

def validate_safety_compliance(state: MicrobiocideState):
    # Business logic for regulatory check
    is_compliant = len(state['compliance_docs']) >= 2 and state['toxicity_level'] < 5.0
    return {'validation_status': is_compliant}

def process_procurement(state: MicrobiocideState):
    return {'validation_status': True}

graph = StateGraph(MicrobiocideState)
graph.add_node('validate', validate_safety_compliance)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
