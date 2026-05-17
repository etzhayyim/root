from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RobotProcurementState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_docs: List[str]

def validate_specs(state: RobotProcurementState):
    is_valid = all(k in state['specs'] for k in ['payload', 'dof'])
    return {'validation_passed': is_valid}

def check_compliance(state: RobotProcurementState):
    return {'compliance_docs': ['ISO-10218-1', 'CE-Mark']}

graph = StateGraph(RobotProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()