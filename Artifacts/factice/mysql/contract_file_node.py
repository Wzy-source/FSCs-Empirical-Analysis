from .dao.contract_file import ContractFile


class ContractFileNode:
    def __init__(self, contract_file: ContractFile = None, id=0, chain=None, address=None, name=None, is_factory=False,
                 is_created=False,
                 compiler=None, balance=None, txcount=0, create_date=None, fixed=False, children=None):
        if contract_file is not None:
            self.id: int = contract_file.id
            self.chain: str = contract_file.chain
            self.address: str = contract_file.address
            self.name: str = contract_file.name
            self.is_factory: bool = contract_file.is_factory
            self.is_created: bool = contract_file.is_created
            self.compiler: str = contract_file.compiler
            self.balance: str = contract_file.balance
            self.txcount: int = contract_file.txcount
            self.create_date: str = contract_file.create_date
            self.fixed: bool = contract_file.fixed
            self.children: list = []
        else:
            if children is None:
                children = []
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
            self.fixed: bool = fixed
            self.children: list = children

    def convert(self, dictionary: dict):
        for key, value in dictionary.items():
            setattr(self, key, value)
        return self
