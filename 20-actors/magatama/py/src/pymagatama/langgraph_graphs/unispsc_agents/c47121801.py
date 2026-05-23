from typing import TypedDict
from langgraph.graph import StateGraph, END

class CleaningToolState(TypedDict):
    material: str
    is_antistatic: bool
    compliance_checked: bool

def check_material_safety(state: CleaningToolState):
    state['compliance_checked'] = state['material'] in ['Microfiber', 'Cotton', 'Synthetic Fiber']
    return state

def validate_antistatic(state: CleaningToolState):
    if state.get('is_antistatic') is False:
        print('Warning: Non-antistatic tool detected for sensitive equipment.')
    return state

graph = StateGraph(CleaningToolState)
graph.add_node('check_material', check_material_safety)
graph.add_node('validate_esd', validate_antistatic)
graph.set_entry_point('check_material')
graph.add_edge('check_material', 'validate_esd')
graph.add_edge('validate_esd', END)
graph = graph.compile()
