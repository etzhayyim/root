from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class IVRState(TypedDict):
    requirements: List[str]
    validation_passed: bool
    deployment_ready: bool

def validate_ivr_specs(state: IVRState):
    state['validation_passed'] = len(state['requirements']) > 0
    return {'validation_passed': state['validation_passed']}

def check_deployment_readiness(state: IVRState):
    state['deployment_ready'] = state['validation_passed']
    return {'deployment_ready': state['deployment_ready']}

graph = StateGraph(IVRState)
graph.add_node('validate', validate_ivr_specs)
graph.add_node('deploy', check_deployment_readiness)
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph.set_entry_point('validate')
graph = graph.compile()
