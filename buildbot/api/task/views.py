from fastapi import APIRouter

from buildbot.api.task.schema import CreateTaskRequest, CreateTaskResponse

router = APIRouter()


@router.post("/", response_model=CreateTaskResponse)
async def send_echo_message(
    task: CreateTaskRequest,
) -> CreateTaskResponse:
    """
    Sends echo back to user.

    :param incoming_message: incoming message.
    :returns: message same as the incoming.
    """
    return CreateTaskResponse(task_id="WIP")
