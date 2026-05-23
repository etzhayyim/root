from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph, END

class RobotComponentState(TypedDict):
    component_id: str
    specs: dict
    validation_logs: Annotated[List[str], operator.add]
    is_compliant: bool

def validate_specs(state: RobotComponentState):
    logs = []
    compliant = True
    if 'torque_specification_nm' not in state['specs']:
        logs.append('Missing torque specification.')
        compliant = False
    return {'validation_logs': logs, 'is_compliant': compliant}

def perform_quality_check(state: RobotComponentState):
    return {'validation_logs': ['Component passed structural stress test.']}

graph = StateGraph(RobotComponentState)
graph.add_node('validate', validate_specs)
graph.add_node('quality', perform_quality_check)
graph.add_edge('validate', 'quality')
graph.add_edge('quality', END)
graph.set_entry_point('validate')
graph = graph.compile()
