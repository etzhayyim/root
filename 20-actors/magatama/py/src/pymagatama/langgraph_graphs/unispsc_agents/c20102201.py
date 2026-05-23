from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CylinderSpec(TypedDict):
    pressure_mpa: float
    bore_mm: float
    status: str
    validation_logs: List[str]

def validate_pressure(state: CylinderSpec) -> CylinderSpec:
    if state['pressure_mpa'] > 70.0:
        state['status'] = 'HIGH_PRESSURE_REVIEW'
        state['validation_logs'].append('High pressure alert: Safety validation required')
    else:
        state['status'] = 'APPROVED'
    return state

def check_dimensions(state: CylinderSpec) -> CylinderSpec:
    if state['bore_mm'] <= 0:
        state['status'] = 'REJECTED'
        state['validation_logs'].append('Invalid bore diameter')
    return state

builder = StateGraph(CylinderSpec)
builder.add_node('validate_pressure', validate_pressure)
builder.add_node('check_dimensions', check_dimensions)
builder.add_edge('validate_pressure', 'check_dimensions')
builder.add_edge('check_dimensions', END)
builder.set_entry_point('validate_pressure')
graph = builder.compile()
