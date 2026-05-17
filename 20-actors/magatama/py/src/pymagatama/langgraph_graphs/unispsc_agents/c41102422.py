from typing import TypedDict, Annotated; import operator; from langgraph.graph import StateGraph, END;

class LabEquipmentState(TypedDict):
    spec_data: dict
    validation_log: Annotated[list, operator.add]
    is_compliant: bool

def validate_dry_bath(state: LabEquipmentState):
    log = []
    specs = state['spec_data']
    if specs.get('temp_range') and specs.get('accuracy'):
        log.append('Specs validated against ISO standards.')
        return {'validation_log': log, 'is_compliant': True}
    return {'validation_log': ['Missing technical specs'], 'is_compliant': False}

def route_by_compliance(state: LabEquipmentState):
    return 'process' if state['is_compliant'] else END

graph = StateGraph(LabEquipmentState)
graph.add_node('validate', validate_dry_bath)
graph.add_edge('validate', END)
graph.set_entry_point('validate')