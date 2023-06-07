messages = {
    "ServiceExists": "Service name already exists",
    "ServiceNameEmpty": "Service name cannot be empty",
    "ServiceDevSupport": "Service Driver type not supported",
    "ServiceCreateSuccess": "Successfully created the service"
}


def lang(message):
    if message in messages:
        return messages[message]
    return message
