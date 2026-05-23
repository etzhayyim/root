from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AthleticWearState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: AthleticWearState):
    required = ['material', 'moisture_management']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed, 'compliance_report': 'Passed' if passed else 'Incomplete'}

def finalize_procurement(state: AthleticWearState):
    return {'compliance_report': 'Ready for sourcing'}

graph = StateGraph(AthleticWearState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
