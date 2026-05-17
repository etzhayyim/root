from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ResinState(TypedDict):
    material_id: str
    viscosity: float
    curing_temp: float
    validation_log: Annotated[Sequence[str], operator.add]
    status: str

def validate_viscosity(state: ResinState):
    if 500 <= state['viscosity'] <= 5000:
        return {'validation_log': ['Viscosity within range'], 'status': 'PROCESSING'}
    return {'validation_log': ['Viscosity deviation detected'], 'status': 'REJECTED'}

def process_curing(state: ResinState):
    if state['status'] == 'PROCESSING':
        if state['curing_temp'] < 150:
            return {'validation_log': ['Curing parameters approved'], 'status': 'APPROVED'}
        return {'validation_log': ['High-temp risk flagged'], 'status': 'REVIEW_REQUIRED'}
    return {'status': state['status']}

graph = StateGraph(ResinState)
graph.add_node('validate', validate_viscosity)
graph.add_node('cure', process_curing)
graph.set_entry_point('validate')
graph.add_edge('validate', 'cure')
graph.add_edge('cure', END)
graph = graph.compile()