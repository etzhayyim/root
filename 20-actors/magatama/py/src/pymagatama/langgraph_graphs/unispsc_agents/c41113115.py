from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class RadonProcurementState(TypedDict):
    sensor_id: str
    calibration_status: bool
    safety_compliance: bool
    inspection_report: str

class WorkflowManager:
    def validate_calibration(self, state: RadonProcurementState):
        print(f'Validating calibration for {state['sensor_id']}')
        return {'calibration_status': True}

    def check_nrc_regs(self, state: RadonProcurementState):
        print('Verifying nuclear regulatory compliance')
        return {'safety_compliance': True}

manager = WorkflowManager()
graph = StateGraph(RadonProcurementState)
graph.add_node('calibrate', manager.validate_calibration)
graph.add_node('safety_check', manager.check_nrc_regs)
graph.set_entry_point('calibrate')
graph.add_edge('calibrate', 'safety_check')
graph.add_edge('safety_check', END)
app = graph.compile()