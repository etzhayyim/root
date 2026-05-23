from typing import TypedDict
from langgraph.graph import StateGraph, END

class UltrasoundLotionState(TypedDict):
    spec_data: dict
    approved: bool
    validation_log: list

def validate_compliance(state: UltrasoundLotionState):
    log = []
    required = ['Acoustic Impedance', 'Biocompatibility Certificate']
    valid = all(key in state['spec_data'] for key in required)
    log.append('Compliance check passed' if valid else 'Missing required specifications')
    return {'approved': valid, 'validation_log': log}

def quality_check(state: UltrasoundLotionState):
    is_hypo = state['spec_data'].get('Hypoallergenic Testing', False)
    return {'approved': is_hypo, 'validation_log': state['validation_log'] + ['Hypoallergenic verified']}

graph = StateGraph(UltrasoundLotionState)
graph.add_node('compliance', validate_compliance)
graph.add_node('quality', quality_check)
graph.add_edge('compliance', 'quality')
graph.add_edge('quality', END)
graph.set_entry_point('compliance')
graph = graph.compile()
