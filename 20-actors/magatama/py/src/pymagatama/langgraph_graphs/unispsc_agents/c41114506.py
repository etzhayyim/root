from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class SpherometerState(TypedDict):
    serial_number: str
    calibration_date: str
    is_verified: bool
    errors: List[str]

def validate_calibration(state: SpherometerState):
    # Business logic for calibration verification
    state['is_verified'] = bool(state['calibration_date'])
    if not state['is_verified']:
        state['errors'].append('Invalid calibration date')
    return state

def generate_qc_report(state: SpherometerState):
    print(f'Generating report for {state.get('serial_number')}')
    return state

graph = StateGraph(SpherometerState)
graph.add_node('validate', validate_calibration)
graph.add_node('report', generate_qc_report)
graph.set_entry_point('validate')
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph = graph.compile()
