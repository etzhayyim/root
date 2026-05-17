from typing import TypedDict
from langgraph.graph import StateGraph, END

class StructureState(TypedDict):
    load_capacity: float
    safety_check: bool
    compliance_docs: list

def validate_structural_specs(state: StructureState):
    if state['load_capacity'] >= 500:
        return {'safety_check': True}
    return {'safety_check': False}

def finalize_build(state: StructureState):
    return {'compliance_docs': ['ISO-Structural-Cert-2024']}

graph = StateGraph(StructureState)
graph.add_node('validate', validate_structural_specs)
graph.add_node('finalize', finalize_build)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()