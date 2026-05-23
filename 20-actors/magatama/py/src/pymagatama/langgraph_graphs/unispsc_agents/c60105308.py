from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TrainingState(TypedDict):
    material_type: str
    participant_count: int
    is_digital: bool
    validation_errors: List[str]

def validate_materials(state: TrainingState):
    errors = []
    if not state.get('material_type'):
        errors.append('Missing material type')
    return {'validation_errors': errors}

def route_by_type(state: TrainingState):
    return 'process_digital' if state['is_digital'] else 'process_physical'

graph = StateGraph(TrainingState)
graph.add_node('validate', validate_materials)
graph.add_node('process_digital', lambda s: s)
graph.add_node('process_physical', lambda s: s)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_type)
graph.add_edge('process_digital', END)
graph.add_edge('process_physical', END)
graph = graph.compile()
