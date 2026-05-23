from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class AdhesiveState(TypedDict):
    specification_id: str
    viscosity: float
    curing_params: dict
    validation_passed: bool
    error_logs: List[str]

def validate_viscosity(state: AdhesiveState):
    passed = 100 <= state['viscosity'] <= 5000
    return {'validation_passed': passed}

def process_curing(state: AdhesiveState):
    if state['validation_passed']:
        return {'curing_params': {'method': 'heat', 'duration': 3600}}
    return {'error_logs': ['Viscosity out of bounds']}

graph = StateGraph(AdhesiveState)
graph.add_node('validate', validate_viscosity)
graph.add_node('cure', process_curing)
graph.set_entry_point('validate')
graph.add_edge('validate', 'cure')
graph.add_edge('cure', END)
app = graph.compile()
