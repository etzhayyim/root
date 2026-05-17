from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ServoState(TypedDict):
    spec_data: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_specs(state: ServoState):
    specs = state['spec_data']
    logs = []
    if specs.get('torque', 0) < 0: logs.append('Error: Invalid torque')
    return {'validation_logs': logs, 'is_compliant': len(logs) == 0}

def check_export_control(state: ServoState):
    return {'validation_logs': ['Checking dual-use export protocols...']}

graph = StateGraph(ServoState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_export_control)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
compile_graph = graph.compile()