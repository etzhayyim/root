from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph, END

class AdhesiveState(TypedDict):
    composition_id: str
    viscosity: float
    safety_check_passed: bool
    log: Annotated[List[str], operator.add]

def validate_viscosity(state: AdhesiveState):
    passed = 100 <= state['viscosity'] <= 5000
    return {'safety_check_passed': passed, 'log': [f'Viscosity check: {passed}']}

def prepare_logistics(state: AdhesiveState):
    return {'log': ['Logistics prep complete for hazardous shipping']}

graph = StateGraph(AdhesiveState)
graph.add_node('validate', validate_viscosity)
graph.add_node('logistics', prepare_logistics)
graph.set_entry_point('validate')
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)

# Compilation
app = graph.compile()