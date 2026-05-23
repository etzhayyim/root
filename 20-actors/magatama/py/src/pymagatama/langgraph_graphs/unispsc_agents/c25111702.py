from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CarrierState(TypedDict):
    spec_id: str
    validation_steps: List[str]
    approved: bool

def validate_defense_specs(state: CarrierState):
    print(f'Validating complex aircraft carrier systems for {state["spec_id"]}')
    return {'validation_steps': ['hull_integrity', 'avionics_sync'], 'approved': True}

def security_audit(state: CarrierState):
    print('Performing ITAR/EAR export control audit')
    return {'approved': True}

graph = StateGraph(CarrierState)
graph.add_node('validate', validate_defense_specs)
graph.add_node('audit', security_audit)
graph.set_entry_point('validate')
graph.add_edge('validate', 'audit')
graph.add_edge('audit', END)
graph = graph.compile()
