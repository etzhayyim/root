from langgraph.graph import StateGraph, END
from typing import TypedDict

class TitaniumState(TypedDict):
    material_grade: str
    weld_inspection_report: dict
    approved: bool

def validate_material(state: TitaniumState):
    state['approved'] = state['material_grade'] == 'Grade 5 Custom'
    return state

def check_weld_integrity(state: TitaniumState):
    if state.get('weld_inspection_report', {}).get('pass'):
        state['approved'] = True
    else:
        state['approved'] = False
    return state

graph = StateGraph(TitaniumState)
graph.add_node('validate', validate_material)
graph.add_node('weld_check', check_weld_integrity)
graph.set_entry_point('validate')
graph.add_edge('validate', 'weld_check')
graph.add_edge('weld_check', END)
graph = graph.compile()