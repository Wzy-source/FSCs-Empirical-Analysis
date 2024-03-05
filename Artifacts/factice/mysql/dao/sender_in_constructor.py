class SenderInConstructor:
    def __init__(self, id=-1, chain=None, address=None, process_start=0, process_end=0,
                 execute_time=0, crashed=False, has_source_code=False, has_issue=False):
        self.id: int = id
        self.address: str = address
        self.chain: str = chain
        self.process_start: int = process_start
        self.process_end: int = process_end
        self.execute_time: int = execute_time
        self.crashed: bool = crashed
        self.has_source_code: bool = has_source_code
        self.has_issue: bool = has_issue

    def convert(self, dictionary: dict):
        for key, value in dictionary.items():
            setattr(self, key, value)
        return self
