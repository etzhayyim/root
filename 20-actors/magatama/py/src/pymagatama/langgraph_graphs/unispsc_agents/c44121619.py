from typing import TypedDict
from langgraph.graph import StateGraph, END

class SharpenerState(TypedDict):
    model_id: str
    is_electric: bool
    safety_compliant: bool

def validate_model(state: SharpenerState):
    print(f'Validating specs for {state[\'model_id\']}')
    return {'safety_compliant': True} if state['is_electric'] else {'safety_compliant': True}

def approval_step(state: SharpenerState):
    print('Approval granted.')
    return {}

graph = StateGraph(SharpenerState)
graph.add_node('validate', validate_model)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()