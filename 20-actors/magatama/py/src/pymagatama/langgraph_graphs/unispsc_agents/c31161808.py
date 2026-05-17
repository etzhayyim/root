from typing import TypedDict
from langgraph.graph import StateGraph, END

class WasherState(TypedDict):
    spec: dict
    validated: bool

def validate_dimension(state: WasherState):
    s = state['spec']
    valid = 'outer_diameter' in s and 'inner_diameter' in s and s['outer_diameter'] > s['inner_diameter']
    return {'validated': valid}

def check_compliance(state: WasherState):
    return {'validated': state['validated'] and state['spec'].get('standard') is not None}

graph = StateGraph(WasherState)
graph.add_node('dimension_check', validate_dimension)
graph.add_node('compliance_check', check_compliance)
graph.set_entry_point('dimension_check')
graph.add_edge('dimension_check', 'compliance_check')
graph.add_edge('compliance_check', END)
app = graph.compile()