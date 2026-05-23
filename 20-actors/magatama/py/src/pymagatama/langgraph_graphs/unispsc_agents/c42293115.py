from typing import TypedDict
from langgraph.graph import StateGraph, END

class TrachealRetractorState(TypedDict):
    spec_data: dict
    validation_results: list
    is_compliant: bool

def validate_specs(state: TrachealRetractorState):
    required = ['Material Grade', 'Sterility Certification', 'CE Marking']
    compliance = all(key in state['spec_data'] for key in required)
    return {'validation_results': ['Specs verified'], 'is_compliant': compliance}

def route_by_compliance(state: TrachealRetractorState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(TrachealRetractorState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
