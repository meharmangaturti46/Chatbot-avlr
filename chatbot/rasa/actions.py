from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

class ActionLeaveApply(Action):
    def name(self) -> Text:
        return "action_leave_apply"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        leave_type = tracker.get_slot("leave_type")
        start_date = tracker.get_slot("start_date")
        end_date = tracker.get_slot("end_date")
        dispatcher.utter_message(text=f"Requesting {leave_type or 'leave'} from {start_date} to {end_date}. (This would be processed in HRMS backend.)")
        return []

class ActionLeaveStatus(Action):
    def name(self) -> Text:
        return "action_leave_status"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Fetching your latest leave status. (This would be processed in HRMS backend.)")
        return []

class ActionLeaveBalance(Action):
    def name(self) -> Text:
        return "action_leave_balance"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="You have 12 annual leaves and 7 sick leaves remaining. (Sample data)")
        return []

class ActionPayslipLatest(Action):
    def name(self) -> Text:
        return "action_payslip_latest"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Your latest payslip is available at: [Payslip Link](#)")
        return []

# ... (Add other action classes for each intent as needed) ...