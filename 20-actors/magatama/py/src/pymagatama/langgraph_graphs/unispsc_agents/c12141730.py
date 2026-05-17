from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ResinState(TypedDict):
    material_code: str
    purity_level: float
    validation_passed: bool
    steps: List[str]

def validate_resin(state: ResinState):
    if state['purity_level'] >= 0.99:
        return {'validation_passed': True, 'steps': state['steps'] + ['purity_validated']}
    return {'validation_passed': False, 'steps': state['steps'] + ['purity_failed']}

def process_workflow(state: ResinState):
    return {'steps': state['steps'] + ['workflow_completed']}

graph = StateGraph(ResinState)
graph.add_node('validate', validate_resin)
graph.add_node('workflow', process_workflow)
graph.add_edge('validate', 'workflow')
graph.add_edge('workflow', END)
graph.set_entry_point('validate')
graph = graph.compile()