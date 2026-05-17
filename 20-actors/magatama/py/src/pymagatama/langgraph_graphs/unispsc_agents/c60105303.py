from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class JobTrainingState(TypedDict):
    materials: List[str]
    validation_errors: List[str]
    is_approved: bool

def validate_material(state: JobTrainingState):
    errors = []
    for m in state['materials']:
        if len(m) < 10:
            errors.append(f'Material too short: {m}')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(JobTrainingState)
graph.add_node('validate', validate_material)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()