from typing import TypedDict
from langgraph.graph import StateGraph, END

class GarmentState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: GarmentState):
    # Simulate spec validation logic
    state['approved'] = 'material' in state['specs'] and 'size' in state['specs']
    return state

def final_check(state: GarmentState):
    print('Proceeding to procurement workflow')
    return {'approved': state['approved']}

graph = StateGraph(GarmentState)
graph.add_node('validate', validate_specs)
graph.add_node('final', final_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'final')
graph.add_edge('final', END)
graph = graph.compile()
