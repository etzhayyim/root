from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class GameProcurementState(TypedDict):
    title: str
    platform: str
    compliance_checks: List[str]
    approved: bool

def validate_platform(state: GameProcurementState):
    state['compliance_checks'].append('Platform validated')
    return {'compliance_checks': state['compliance_checks']}

def check_age_rating(state: GameProcurementState):
    state['compliance_checks'].append('Rating verified')
    return {'compliance_checks': state['compliance_checks']}

def finalize_procurement(state: GameProcurementState):
    state['approved'] = True
    return {'approved': True}

graph = StateGraph(GameProcurementState)
graph.add_node('validate_platform', validate_platform)
graph.add_node('check_age_rating', check_age_rating)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate_platform')
graph.add_edge('validate_platform', 'check_age_rating')
graph.add_edge('check_age_rating', 'finalize')
graph.add_edge('finalize', END)
app = graph.compile()
