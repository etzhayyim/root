from typing import TypedDict, List
from langgraph.graph import StateGraph, END
class TelegraphState(TypedDict):
    equipment_id: str
    specs: dict
    validation_passed: bool
def validate_telecom_standards(state: TelegraphState) -> TelegraphState:
    print(f'Validating specs for {state['equipment_id']}')
    state['validation_passed'] = True
    return state
def route_verification(state: TelegraphState) -> str:
    return 'validate' if state['validation_passed'] else END
graph = StateGraph(TelegraphState)
graph.add_node('validate', validate_telecom_standards)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()