from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict

class DesiccantState(TypedDict):
    specs: Dict
    compliance_check: bool
    approved: bool

def validate_specs(state: DesiccantState):
    absorption = state['specs'].get('absorption_capacity', 0)
    state['compliance_check'] = absorption > 0.2
    return state

def approval_logic(state: DesiccantState):
    state['approved'] = state['compliance_check']
    return state

graph = StateGraph(DesiccantState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_logic)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()