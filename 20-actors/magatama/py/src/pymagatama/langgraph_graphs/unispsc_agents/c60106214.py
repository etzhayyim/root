from typing import TypedDict
from langgraph.graph import StateGraph, END

class RobotKitState(TypedDict):
    kit_id: str
    compliance_checked: bool
    safety_verified: bool

def validate_specs(state: RobotKitState):
    print(f'Validating specs for {state[\'kit_id\']}')
    return {'compliance_checked': True}

def verify_safety(state: RobotKitState):
    print('Checking safety standards...')
    return {'safety_verified': True}

workflow = StateGraph(RobotKitState)
workflow.add_node('validate', validate_specs)
workflow.add_node('safety', verify_safety)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'safety')
workflow.add_edge('safety', END)
graph = workflow.compile()