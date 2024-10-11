class ContractFile:
    def __init__(self, id=-1, chain=None, address=None, name=None, is_factory=False, is_created=False,
                 compiler=None, balance=None, txcount=0, create_date=None, source_code=None, fixed=False, is_factory_truth=False):
        self.id: int = id
        self.chain: str = chain
        self.address: str = address
        self.name: str = name
        self.is_factory: bool = is_factory
        self.is_created: bool = is_created
        self.compiler: str = compiler
        self.balance: str = balance
        self.txcount: int = txcount
        self.create_date: str = create_date
        self.source_code: str = source_code
        self.fixed: bool = fixed
        self.is_factory_truth: bool = is_factory_truth

    def convert(self, dictionary: dict):
        for key, value in dictionary.items():
            setattr(self, key, value)
        return self
