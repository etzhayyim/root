from typing import TypedDict
from langgraph.graph import StateGraph, END

class CPAPState(TypedDict):
    device_id: str
    pressure_calibration: float
    compliance_report: str

def validate_calibration(state: CPAPState):
    if 4.0 <= state['pressure_calibration'] <= 25.0:
        return {'compliance_report': 'Validated'}
    return {'compliance_report': 'OutOfRange'}

def finalize_procurement(state: CPAPState):
    return {'compliance_report': 'Finalized'}

graph = StateGraph(CPAPState)
graph.add_node('validate', validate_calibration)
graph.add_node('finish', finalize_procurement)
graph.add_edge('validate', 'finish')
graph.add_edge('finish', END)
graph.set_entry_point('validate')
graph = graph.compile()
