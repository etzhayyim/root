from typing import TypedDict
from langgraph.graph import StateGraph, END

class MathKitState(TypedDict):
    kit_components: list
    standards_compliant: bool
    approved: bool

def validate_components(state: MathKitState):
    required = ['geometry_set', 'calculator', 'graph_paper']
    compliance = all(item in state['kit_components'] for item in required)
    return {'standards_compliant': compliance}

def approval_step(state: MathKitState):
    return {'approved': state['standards_compliant']}

graph = StateGraph(MathKitState)
graph.add_node('validate', validate_components)
graph.add_node('approve', approval_step)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph.compile()
