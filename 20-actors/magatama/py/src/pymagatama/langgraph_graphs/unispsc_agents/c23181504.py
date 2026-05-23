from typing import TypedDict
from langgraph.graph import StateGraph, END

class CleaningEquipmentState(TypedDict):
    equipment_id: str
    spec_data: dict
    validation_passed: bool

def validate_specs(state: CleaningEquipmentState):
    # Business logic for equipment validation
    pressure = state['spec_data'].get('pressure', 0)
    state['validation_passed'] = pressure > 0 and pressure < 500
    return state

def safety_check(state: CleaningEquipmentState):
    # Safety protocols for heavy machinery
    print(f'Checking safety standards for {state.get('equipment_id')}')
    return state

graph = StateGraph(CleaningEquipmentState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
