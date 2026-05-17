from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class MiningState(TypedDict):
    equipment_id: str
    capacity_check: bool
    safety_audit_passed: bool
    procurement_approved: bool

def validate_equipment(state: MiningState):
    print(f'Validating equipment: {state['equipment_id']}')
    return {'capacity_check': True}

def conduct_safety_audit(state: MiningState):
    print(f'Auditing safety for: {state['equipment_id']}')
    return {'safety_audit_passed': True}

graph = StateGraph(MiningState)
graph.add_node('validate', validate_equipment)
graph.add_node('audit', conduct_safety_audit)
graph.set_entry_point('validate')
graph.add_edge('validate', 'audit')
graph.add_edge('audit', END)
app = graph.compile()