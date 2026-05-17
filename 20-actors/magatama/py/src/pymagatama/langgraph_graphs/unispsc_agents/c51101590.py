from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MaintenanceState(TypedDict):
    equipment_id: str
    validation_required: bool
    history: Annotated[Sequence[str], operator.add]

def validate_instrument(state: MaintenanceState):
    print(f'Validating instrument: {state.equipment_id}')
    return {'history': ['Validation protocol complete']}

def perform_calibration(state: MaintenanceState):
    print(f'Calibrating instrument: {state.equipment_id}')
    return {'history': ['Calibration verified']}

graph = StateGraph(MaintenanceState)
graph.add_node('validate', validate_instrument)
graph.add_node('calibrate', perform_calibration)
graph.add_edge('validate', 'calibrate')
graph.set_entry_point('validate')
graph.add_edge('calibrate', END)
graph = graph.compile()