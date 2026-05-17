from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ReagentProcessState(TypedDict):
    material_id: str
    purity_level: float
    safety_clearance: bool
    validation_log: Annotated[Sequence[str], operator.add]

def validate_purity(state: ReagentProcessState) -> ReagentProcessState:
    if state['purity_level'] < 99.0:
        return {'validation_log': ['Purity level below standard']}
    return {'validation_log': ['Purity verified']}

def check_safety_compliance(state: ReagentProcessState) -> ReagentProcessState:
    if not state['safety_clearance']:
        return {'validation_log': ['Safety compliance missing']}
    return {'validation_log': ['Safety compliant']}

def build_reagent_graph():
    workflow = StateGraph(ReagentProcessState)
    workflow.add_node('validate_purity', validate_purity)
    workflow.add_node('check_safety', check_safety_compliance)
    workflow.set_entry_point('validate_purity')
    workflow.add_edge('validate_purity', 'check_safety')
    workflow.add_edge('check_safety', END)
    return workflow.compile()

graph = build_reagent_graph()