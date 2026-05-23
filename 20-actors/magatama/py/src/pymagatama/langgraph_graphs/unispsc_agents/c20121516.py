from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class RobotBearingState(TypedDict):
    part_number: str
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_bearing_specs(state: RobotBearingState):
    specs = state['spec_data']
    errors = []
    if specs.get('rotational_accuracy_class', 0) < 5:
        errors.append('Precision class below industrial standard')
    return {'validation_passed': len(errors) == 0, 'error_log': errors}

def route_to_qa(state: RobotBearingState):
    return 'QA_NODE' if state['validation_passed'] else 'REJECT_NODE'

graph = StateGraph(RobotBearingState)
graph.add_node('VALIDATE', validate_bearing_specs)
graph.add_node('QA_NODE', lambda s: {'validation_passed': True})
graph.add_node('REJECT_NODE', lambda s: {'validation_passed': False})
graph.set_entry_point('VALIDATE')
graph.add_conditional_edges('VALIDATE', route_to_qa)
graph.add_edge('QA_NODE', END)
graph.add_edge('REJECT_NODE', END)
compiled_graph = graph.compile()
