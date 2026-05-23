from typing import TypedDict
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_specs(state: BearingState):
    required = ['load_rating', 'material']
    return {'is_compliant': all(k in state['spec_data'] for k in required)}

def proceed_to_procurement(state: BearingState):
    return 'procurement_ready'

graph = StateGraph(BearingState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', proceed_to_procurement)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
app = graph.compile()
