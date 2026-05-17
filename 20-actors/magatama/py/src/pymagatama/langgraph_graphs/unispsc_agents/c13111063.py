from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class MineralState(TypedDict):
    survey_data: dict
    drilling_plan: dict
    risk_assessment: List[str]
    status: str

def validate_survey(state: MineralState) -> MineralState:
    if not state['survey_data'].get('depth'):
        state['status'] = 'NEEDS_DATA'
    else:
        state['status'] = 'VALIDATED'
    return state

def plan_drilling(state: MineralState) -> MineralState:
    if state['status'] == 'VALIDATED':
        state['drilling_plan'] = {'method': 'rotary', 'safety_check': True}
    return state

graph = StateGraph(MineralState)
graph.add_node('validate', validate_survey)
graph.add_node('plan', plan_drilling)
graph.set_entry_point('validate')
graph.add_edge('validate', 'plan')
graph.add_edge('plan', END)
graph = graph.compile()