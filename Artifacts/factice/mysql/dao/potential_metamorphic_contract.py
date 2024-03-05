class PotentialMetamorphicContract:
    def __init__(self, id=-1, address=None, chain=None, create_type='unknown', bytecode=None,
                 decompiled_code=None, dynamic_init_code=False, implement_setter=False,
                 implement_getter=False, pattern1=False, pattern2=False):
        self.id: int = id
        self.address: str = address
        self.chain: str = chain
        self.create_type: str = create_type
        self.bytecode: str = bytecode
        self.decompiled_code: str = decompiled_code
        self.dynamic_init_code: bool = dynamic_init_code
        self.implement_setter: bool = implement_setter
        self.implement_getter: bool = implement_getter
        self.pattern1: bool = pattern1
        self.pattern2: bool = pattern2

    def convert(self, dictionary: dict):
        for key, value in dictionary.items():
            setattr(self, key, value)
        return self
