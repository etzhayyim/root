from typing import TypedDict
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    spec_data: dict
    validation_results: list
    is_compliant: bool

def validate_specs(state: RobotState):
    specs = state['spec_data']
    results = []
    if specs.get('payload_kg', 0) > 50:
        results.append('Heavy duty classification required')
    return {'validation_results': results, 'is_compliant': True}

graph = StateGraph(RobotState)
graph.add_node('validator', validate_specs)
graph.set_entry_point('validator')
graph.add_edge('validator', END)
graph = graph.compile()
