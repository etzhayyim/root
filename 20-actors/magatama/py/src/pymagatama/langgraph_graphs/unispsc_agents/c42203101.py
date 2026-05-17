from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MicrodosimeterState(TypedDict):
    device_id: str
    calibration_data: dict
    compliance_docs: List[str]
    validation_passed: bool

def validate_compliance(state: MicrodosimeterState):
    state['validation_passed'] = all(doc in state['compliance_docs'] for doc in ['ISO-IEC-17025', 'Safety-Certificate'])
    print(f'Compliance status: {state['validation_passed']}')
    return 'process_calibration'

def process_calibration(state: MicrodosimeterState):
    print('Processing radiation energy linearity curves...')
    return 'end'

graph = StateGraph(MicrodosimeterState)
graph.add_node('validate_compliance', validate_compliance)
graph.add_node('process_calibration', process_calibration)
graph.set_entry_point('validate_compliance')
graph.add_edge('validate_compliance', 'process_calibration')
graph.add_edge('process_calibration', END)
graph.add_edge('process_calibration', END)
app = graph.compile()