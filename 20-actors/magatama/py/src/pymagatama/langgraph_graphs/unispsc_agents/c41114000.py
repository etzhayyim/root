from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class GeotechnicalState(TypedDict):
    equipment_id: str
    calibration_date: str
    validation_status: str
    sensor_data: List[float]

def validate_specs(state: GeotechnicalState):
    print('Validating calibration data...')
    state['validation_status'] = 'CERTIFIED' if state['calibration_date'] else 'ERROR'
    return state

def process_sensor_logs(state: GeotechnicalState):
    print(f'Processing telemetry for {state['equipment_id']}')
    return state

graph = StateGraph(GeotechnicalState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_sensor_logs)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()