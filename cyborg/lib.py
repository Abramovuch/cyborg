from asyncio import Queue


class QueueDone(object):
    def __init__(self):
        raise RuntimeError("Cannot create instance of QueueDone")