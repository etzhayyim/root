from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SprayerState(TypedDict):
    material: str
    chemical_type: str
    is_compliant: bool

def validate_materials(state: SprayerState) -> SprayerState:
    # Logic to ensure nozzle material resists chemical type
    if state['material'] == 'rubber' and 'acid' in state['chemical_type']:
        state['is_compliant'] = False
    else:
        state['is_compliant'] = True
    return state

workflow = StateGraph(SprayerState)
workflow.add_node('validate', validate_materials)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
