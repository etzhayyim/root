from typing import TypedDict
from langgraph.graph import StateGraph, END

class SprayGraphState(TypedDict):
    spec_data: dict
    validation_log: list
    is_compliant: bool

def validate_specs(state: SprayGraphState):
    specs = state['spec_data']
    logs = []
    if specs.get('pressure', 0) > 3000:
         logs.append('High pressure warning: Ensure safety valve compliance.')
    return {'validation_log': logs, 'is_compliant': True}

def safety_check(state: SprayGraphState):
    # Simulated compliance logic
    return {'is_compliant': True}

graph = StateGraph(SprayGraphState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
