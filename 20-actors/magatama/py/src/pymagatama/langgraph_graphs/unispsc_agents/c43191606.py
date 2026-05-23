from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class TapeDriveState(TypedDict):
    drive_id: str
    specifications: dict
    validation_logs: Annotated[List[str], operator.add]
    is_compliant: bool

def validate_specs(state: TapeDriveState):
    specs = state['specifications']
    logs = []
    compliant = True
    if specs.get('mtbf_hours', 0) < 50000:
        logs.append('Insufficient MTBF for enterprise archival.')
        compliant = False
    return {'validation_logs': logs, 'is_compliant': compliant}

def check_interface(state: TapeDriveState):
    if state['specifications'].get('interface_type') not in ['SAS', 'FC']:
        return {'validation_logs': ['Unsupported interface type.'], 'is_compliant': False}
    return {'validation_logs': ['Interface compliant.'], 'is_compliant': True}

graph = StateGraph(TapeDriveState)
graph.add_node('validate_specs', validate_specs)
graph.add_node('check_interface', check_interface)
graph.set_entry_point('validate_specs')
graph.add_edge('validate_specs', 'check_interface')
graph.add_edge('check_interface', END)
app = graph.compile()
