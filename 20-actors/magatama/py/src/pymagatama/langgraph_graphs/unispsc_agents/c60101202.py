from langgraph.graph import StateGraph, END
from typing import TypedDict, List
class IncentiveChartState(TypedDict):
    theme: str
    slots: int
    paper_stock: str
    approval_status: bool
def validate_theme(state: IncentiveChartState):
    state['approval_status'] = 'Bible' in state['theme']
    return state
def check_material(state: IncentiveChartState):
    return {'approval_status': state['approval_status'] and state['paper_stock'] == 'cardstock'}
builder = StateGraph(IncentiveChartState)
builder.add_node('validate_theme', validate_theme)
builder.add_node('check_material', check_material)
builder.set_entry_point('validate_theme')
builder.add_edge('validate_theme', 'check_material')
builder.add_edge('check_material', END)
graph = builder.compile()
