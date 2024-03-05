class ImplementContractValidation:
    def __init__(self, id=-1, chain=None, address=None, process_start=0, process_end=0, execute_time=0,
                 crashed=False, has_source_code=False, is_clone_based_factory=False, not_check=False,
                 check_addr0=False,check_is_contract=False,check_fn_call=False,external_address=False,
                 internal_address=False,in_whitelist=False):
        self.id: int = id
        self.address: str = address
        self.chain: str = chain
        self.process_start: int = process_start
        self.process_end: int = process_end
        self.execute_time: int = execute_time
        self.crashed: bool = crashed
        self.has_source_code: bool = has_source_code
        self.is_clone_based_factory: bool = is_clone_based_factory
        self.not_check:bool=not_check
        self.check_addr0:bool=check_addr0
        self.check_is_contract:bool=check_is_contract
        self.check_fn_call:bool=check_fn_call
        self.external_address: bool = external_address
        self.internal_address: bool = internal_address
        self.in_whitelist: bool = in_whitelist

    def convert(self, dictionary: dict):
        for key, value in dictionary.items():
            setattr(self, key, value)
        return self
