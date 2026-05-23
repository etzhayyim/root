from typing import TypedDict
from langgraph.graph import StateGraph, END

class AntidoteState(TypedDict):
    batch_id: str
    purity_level: float
    status: str

def validate(state: AntidoteState):
    if state['purity_level'] < 99.9:
        return {'status': 'rejected'}
    return {'status': 'qualified'}

workflow = StateGraph(AntidoteState)
workflow.add_node('validation', validate)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()
