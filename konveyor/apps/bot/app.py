from aiohttp import web
from aiohttp.web import Request, Response
from botbuilder.core import BotFrameworkAdapterSettings, BotFrameworkAdapter
from botbuilder.schema import Activity
import sys
import traceback
from .bot import KonveyorBot
from konveyor.core.azure_utils.config import AzureConfig
from django.conf import settings



# Load configuration using AzureConfig
config = AzureConfig()
# Ensure required Bot Framework settings are present
config.validate_required_config('BOT')
# Bot Framework setup
SETTINGS = BotFrameworkAdapterSettings(
    config.get_setting('MICROSOFT_APP_ID'),
    config.get_setting('MICROSOFT_APP_PASSWORD')
)
ADAPTER = BotFrameworkAdapter(SETTINGS)
BOT = KonveyorBot()

# Error handling
async def on_error(context, error):
    print(f"\n[on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()
    await context.send_activity("The bot encountered an error or bug.")

ADAPTER.on_turn_error = on_error

# Message handler
async def messages(req: Request) -> Response:
    if "application/json" not in req.headers["Content-Type"]:
        return Response(status=415)

    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""

    try:
        response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
        if response:
            return web.json_response(data=response.body, status=response.status)
        return Response(status=200)
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        return Response(status=500)

APP = web.Application()
APP.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    try:
        web.run_app(APP, host="localhost", port=3978)
    except Exception as error:
        raise error