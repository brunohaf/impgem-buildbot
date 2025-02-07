from fastapi import APIRouter

from buildbot.web.api.task.schema import Task, TaskRequest, TaskResponse

router = APIRouter()


@router.post("/", response_model=TaskResponse)
async def send_echo_message(
    task: TaskRequest,
) -> TaskResponse:
    """
    Sends echo back to user.

    :param incoming_message: incoming message.
    :returns: message same as the incoming.
    """
    return incoming_message
