from typing import TypedDict
from langgraph.graph import StateGraph, END

class SlushMachineState(TypedDict):
    capacity: float
    food_safety_cert: bool
    approved: bool

def validate_specs(state: SlushMachineState):
    if state['capacity'] > 0 and state['food_safety_cert']:
        return {'approved': True}
    return {'approved': False}

def deploy_procurement(state: SlushMachineState):
    print(f'Procurement order for capacity {state['capacity']} is set.')

graph = StateGraph(SlushMachineState)
graph.add_node('validate', validate_specs)
graph.add_node('deploy', deploy_procurement)
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()