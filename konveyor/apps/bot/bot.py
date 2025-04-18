from botbuilder.core import TurnContext, ActivityHandler
from botbuilder.schema import ActivityTypes, Activity

class KonveyorBot(ActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        return await turn_context.send_activity(
            Activity(
                type=ActivityTypes.message,
                text=f"You said: {turn_context.activity.text}"
            )
        )

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    Activity(
                        type=ActivityTypes.message,
                        text="Welcome to Konveyor Bot! Type something to get started."
                    )
                )