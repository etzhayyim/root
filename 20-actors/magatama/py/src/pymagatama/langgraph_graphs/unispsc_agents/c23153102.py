from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ServoState(TypedDict):
    part_number: str
    torque_requirement: float
    validation_passed: bool
    log: List[str]

def validate_specs(state: ServoState):
    # Simulate CAD/spec validation logic
    passed = state['torque_requirement'] > 0
    return {'validation_passed': passed, 'log': ['Specs validated']}

def routing_logic(state: ServoState):
    return 'validate' if state['validation_passed'] else END

graph = StateGraph(ServoState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)

app = graph.compile()
