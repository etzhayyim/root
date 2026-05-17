from typing import TypedDict
from langgraph.graph import StateGraph, END

class RefrigeratorState(TypedDict):
    specs: dict
    validation_results: list
    is_compliant: bool

def validate_specs(state: RefrigeratorState):
    required = ['energy_star', 'capacity', 'safety_mark']
    compliance = all(k in state['specs'] for k in required)
    return {'validation_results': ['Checked specs'], 'is_compliant': compliance}

graph = StateGraph(RefrigeratorState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()