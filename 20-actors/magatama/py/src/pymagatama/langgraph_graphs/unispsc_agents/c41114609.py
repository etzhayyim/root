from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ForgingTestState(TypedDict):
    equipment_id: str
    calibration_status: bool
    test_parameters: dict
    validation_report: str

def validate_equipment(state: ForgingTestState):
    if not state.get('calibration_status'):
        return {'validation_report': 'FAILED: Calibration certificate required.'}
    return {'validation_report': 'PASSED: Ready for testing.'}

def conduct_test(state: ForgingTestState):
    return {'validation_report': 'Test conducted on ' + state['equipment_id']}

graph = StateGraph(ForgingTestState)
graph.add_node('validate', validate_equipment)
graph.add_node('test', conduct_test)
graph.set_entry_point('validate')
graph.add_edge('validate', 'test')
graph.add_edge('test', END)
graph = graph.compile()