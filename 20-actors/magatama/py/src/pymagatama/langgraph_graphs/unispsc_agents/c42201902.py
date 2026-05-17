from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class XRaySystemState(TypedDict):
    model_number: str
    luminance_levels: List[float]
    compliance_docs: List[str]
    validated: bool

def validate_system(state: XRaySystemState):
    # Business logic for X-ray viewer safety and calibration checks
    required_docs = ['IEC60601', 'ISO13485']
    all_present = all(doc in state['compliance_docs'] for doc in required_docs)
    return {'validated': all_present}

workflow = StateGraph(XRaySystemState)
workflow.add_node('validate', validate_system)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()