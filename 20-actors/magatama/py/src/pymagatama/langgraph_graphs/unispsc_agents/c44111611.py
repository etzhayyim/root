from typing import TypedDict
from langgraph.graph import StateGraph, END

class MoneyClipState(TypedDict):
    material: str
    finish: str
    force_newtons: float
    validation_passed: bool

def validate_material(state: MoneyClipState):
    valid_materials = ['Stainless Steel', 'Titanium', 'Brass', 'Leather']
    state['validation_passed'] = state['material'] in valid_materials
    print(f'Validating material: {state['material']}')
    return 'check_force'

def check_force(state: MoneyClipState):
    if state['force_newtons'] < 5.0:
        state['validation_passed'] = False
    return 'end'

workflow = StateGraph(MoneyClipState)
workflow.add_node('validate_material', validate_material)
workflow.add_node('check_force', check_force)
workflow.set_entry_point('validate_material')
workflow.add_edge('validate_material', 'check_force')
workflow.add_edge('check_force', END)
graph = workflow.compile()