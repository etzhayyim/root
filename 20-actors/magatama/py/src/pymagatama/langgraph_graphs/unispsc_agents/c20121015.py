from typing import TypedDict, Annotated, List, Union
from langgraph.graph import StateGraph, END

class RobotToolState(TypedDict):
    tool_id: str
    spec_requirements: dict
    validation_log: List[str]
    is_compliant: bool

def validate_tool_specs(state: RobotToolState):
    specs = state['spec_requirements']
    logs = []
    if specs.get('payload_capacity_kg', 0) <= 0:
        logs.append('Error: Invalid payload capacity')
    if specs.get('repeatability_mm', 1.0) > 0.5:
        logs.append('Warning: Low precision for assembly')
    return {'validation_log': logs, 'is_compliant': len(logs) == 0}

def generate_assembly_config(state: RobotToolState):
    config = f'Configuring gripper {state['tool_id']} for precision assembly...'
    return {'validation_log': state['validation_log'] + [config]}

graph = StateGraph(RobotToolState)
graph.add_node('validate', validate_tool_specs)
graph.add_node('configure', generate_assembly_config)
graph.set_entry_point('validate')
graph.add_edge('validate', 'configure')
graph.add_edge('configure', END)
graph = graph.compile()
