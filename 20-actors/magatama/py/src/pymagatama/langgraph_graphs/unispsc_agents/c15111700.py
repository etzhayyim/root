from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class LubricantState(TypedDict):
    product_id: str
    viscosity_check: bool
    safety_compliance: bool
    log: List[str]

def validate_viscosity(state: LubricantState) -> dict:
    state['viscosity_check'] = True
    state['log'].append('Viscosity within specs.')
    return state

def check_safety(state: LubricantState) -> dict:
    state['safety_compliance'] = True
    state['log'].append('MSDS verified.')
    return state

graph = StateGraph(LubricantState)
graph.add_node('validate_viscosity', validate_viscosity)
graph.add_node('check_safety', check_safety)
graph.set_entry_point('validate_viscosity')
graph.add_edge('validate_viscosity', 'check_safety')
graph.add_edge('check_safety', END)

app = graph.compile()
