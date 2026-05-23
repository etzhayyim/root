from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RobotPartState(TypedDict):
    part_id: str
    spec_data: dict
    is_compliant: bool
    validation_log: List[str]

def validate_specs(state: RobotPartState):
    specs = state['spec_data']
    log = []
    compliant = True
    if specs.get('load_capacity', 0) <= 0:
        log.append("Invalid load capacity")
        compliant = False
    return {'is_compliant': compliant, 'validation_log': log}

def export_check(state: RobotPartState):
    # Dual-use export control logic
    return {'validation_log': state['validation_log'] + ["Export control checked"]}

graph = StateGraph(RobotPartState)
graph.add_node("validate", validate_specs)
graph.add_node("export", export_check)
graph.add_edge("validate", "export")
graph.add_edge("export", END)
graph.set_entry_point("validate")
graph = graph.compile()
