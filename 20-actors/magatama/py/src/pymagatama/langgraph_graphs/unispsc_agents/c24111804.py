from typing import TypedDict
from langgraph.graph import StateGraph, END

class CalibrationState(TypedDict):
    tank_id: str
    spec_data: dict
    is_validated: bool

def validate_specs(state: CalibrationState):
    specs = state.get('spec_data', {})
    state['is_validated'] = all(k in specs for k in ['accuracy', 'pressure_rating'])
    print(f'Validating tank {state['tank_id']}...')
    return state

workflow = StateGraph(CalibrationState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
