from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

class GearState(TypedDict):
    spec: dict
    validation_results: Annotated[list, operator.add]
    status: str

def validate_torque(state: GearState):
    torque = state['spec'].get('rated_torque_nm', 0)
    valid = torque > 0
    return {'validation_results': [f'Torque check: {valid}']}

def check_backlash(state: GearState):
    backlash = state['spec'].get('backlash_arcmin', 10)
    valid = backlash <= 5
    return {'validation_results': [f'Backlash precision: {valid}']}

def assemble_status(state: GearState):
    return {'status': 'Validated' if all('True' in r for r in state['validation_results']) else 'Failed'}

graph = StateGraph(GearState)
graph.add_node('torque', validate_torque)
graph.add_node('backlash', check_backlash)
graph.add_node('status', assemble_status)
graph.set_entry_point('torque')
graph.add_edge('torque', 'backlash')
graph.add_edge('backlash', 'status')
graph.add_edge('status', END)
graph = graph.compile()
