from typing import TypedDict
from langgraph.graph import StateGraph, END

class JugState(TypedDict):
    capacity: float
    material: str
    is_food_grade: bool
    validation_status: str

def validate_jug_spec(state: JugState):
    if state['capacity'] <= 0:
        return {'validation_status': 'INVALID_CAPACITY'}
    if state['is_food_grade'] and state['material'] == 'Plastic_Unspecified':
        return {'validation_status': 'CERTIFICATION_REQUIRED'}
    return {'validation_status': 'APPROVED'}

graph = StateGraph(JugState)
graph.add_node('validate', validate_jug_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()