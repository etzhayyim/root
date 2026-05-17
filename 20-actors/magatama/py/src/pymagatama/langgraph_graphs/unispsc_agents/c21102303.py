from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RobotProcessingState(TypedDict):
    assembly_id: str
    spec_check: bool
    compliance_risk: str

def validate_specs(state: RobotProcessingState):
    print(f'Validating robot arm specs for {state['assembly_id']}')
    return {'spec_check': True}

def check_compliance(state: RobotProcessingState):
    print('Checking dual-use export regulations')
    return {'compliance_risk': 'low'}

graph = StateGraph(RobotProcessingState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()