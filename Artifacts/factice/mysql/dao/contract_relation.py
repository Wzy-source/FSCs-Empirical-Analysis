class ContractRelation:
    def __init__(self, id=-1, factory_id=0, created_id=0, create_type=None, tx_hash=None, gas=0, gas_used=0,
                 time_stamp=0):
        self.id: int = id
        self.factory_id: int = factory_id
        self.created_id: int = created_id
        self.create_type: str = create_type
        self.tx_hash: str = tx_hash
        self.gas: int = gas
        self.gas_used: int = gas_used
        self.time_stamp: int = time_stamp

    def convert(self, dictionary: dict):
        for key, value in dictionary.items():
            setattr(self, key, value)
        return self
