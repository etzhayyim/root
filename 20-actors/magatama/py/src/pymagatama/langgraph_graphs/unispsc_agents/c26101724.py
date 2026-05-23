from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GlowPlugState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_logs: List[str]

def validate_specs(state: GlowPlugState):
    required = ['voltage_rating_v', 'heating_time_sec']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed, 'error_logs': [] if passed else ['Missing technical specs']}

def dispatch_procurement(state: GlowPlugState):
    return {'validation_passed': True}

graph = StateGraph(GlowPlugState)
graph.add_node('validate', validate_specs)
graph.add_node('dispatch', dispatch_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'dispatch')
graph.add_edge('dispatch', END)
graph = graph.compile()
