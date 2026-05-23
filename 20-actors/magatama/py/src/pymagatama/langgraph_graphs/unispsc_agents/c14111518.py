from typing import TypedDict, Annotated, List, Union
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class PaperState(TypedDict):
    spec_requirements: dict
    validation_logs: Annotated[List[str], add_messages]
    status: str

def validate_gsm(state: PaperState) -> PaperState:
    gsm = state['spec_requirements'].get('gsm_weight', 0)
    if 60 <= gsm <= 120:
        state['validation_logs'].append(f'GSM {gsm} is within standard range.')
    else:
        state['validation_logs'].append(f'GSM {gsm} warning: outside standard range.')
    return state

def check_certification(state: PaperState) -> PaperState:
    cert = state['spec_requirements'].get('sustainablity_certification')
    if cert in ['FSC', 'PEFC']:
        state['status'] = 'COMPLIANT'
    else:
        state['status'] = 'PENDING_REVIEW'
    return state

graph = StateGraph(PaperState)
graph.add_node('validate_gsm', validate_gsm)
graph.add_node('check_cert', check_certification)
graph.set_entry_point('validate_gsm')
graph.add_edge('validate_gsm', 'check_cert')
graph.add_edge('check_cert', END)
graph = graph.compile()
