from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ScubaState(TypedDict):
    equipment_id: str
    safety_certs: List[str]
    passed_inspection: bool

def validate_safety_protocols(state: ScubaState):
    print(f'Validating certs for: {state["equipment_id"]}')
    state['passed_inspection'] = 'EN250' in state.get('safety_certs', [])
    return state

def route_equipment(state: ScubaState):
    return 'approved' if state['passed_inspection'] else 'rejected'

graph = StateGraph(ScubaState)
graph.add_node('validation', validate_safety_protocols)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()
