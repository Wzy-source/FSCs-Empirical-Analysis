class FSC_Validation:
    def __init__(self, id=-1, contract_file_id=-1, chain=None, address=None, name=None, contain_create_tx=False, is_factory_detect=False,
                 create_tx_hash: str = None):
        self.id: int = id
        self.contract_file_id: int = contract_file_id
        self.chain: str = chain
        self.address: str = address
        self.name: str = name
        self.contain_create_tx: bool = contain_create_tx
        self.is_factory_detect: bool = is_factory_detect
        self.create_txhash: str = create_tx_hash

    def convert(self, dictionary: dict):
        for key, value in dictionary.items():
            setattr(self, key, value)
        return self
