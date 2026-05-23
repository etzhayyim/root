from typing import TypedDict
from langgraph.graph import StateGraph, END

class DevelopmentTankState(TypedDict):
    tank_capacity: int
    is_light_tight: bool
    chemical_resistance_grade: str
    status: str

def validate_specifications(state: DevelopmentTankState):
    if state['tank_capacity'] > 0 and state['is_light_tight']:
        return {'status': 'PASSED'}
    return {'status': 'FAILED'}

workflow = StateGraph(DevelopmentTankState)
workflow.add_node('validation', validate_specifications)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()
