from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SwivelJointState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_risk: str

def validate_specs(state: SwivelJointState):
    required = ['pressure', 'material', 'thread']
    all_present = all(k in state['specs'] for k in required)
    return {'validation_passed': all_present, 'compliance_risk': 'low' if all_present else 'critical'}

def check_compliance(state: SwivelJointState):
    if state.get('material') == 'titanium':
        return {'compliance_risk': 'high'}
    return state

graph = StateGraph(SwivelJointState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()