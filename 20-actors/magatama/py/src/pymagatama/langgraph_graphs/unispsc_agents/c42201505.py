from typing import TypedDict
from langgraph.graph import StateGraph, END

class CTConsoleState(TypedDict):
    specs: dict
    validation_log: list
    is_compliant: bool

def validate_dicom(state: CTConsoleState):
    log = state.get('validation_log', [])
    compliance = state['specs'].get('dicom_version') == '3.0'
    log.append(f'DICOM Compliance identified: {compliance}')
    return {'validation_log': log, 'is_compliant': compliance}

def hardware_inspection(state: CTConsoleState):
    log = state.get('validation_log', [])
    is_secure = state['specs'].get('encryption_enabled', False)
    log.append('Hardware security verified' if is_secure else 'Security failure')
    return {'validation_log': log}

graph = StateGraph(CTConsoleState)
graph.add_node('dicom_check', validate_dicom)
graph.add_node('hw_check', hardware_inspection)
graph.add_edge('dicom_check', 'hw_check')
graph.add_edge('hw_check', END)
graph.set_entry_point('dicom_check')
graph = graph.compile()