class AddressValidation:
    def __init__(self, id=-1, chain=None, address=None, process_start=0, process_end=0, execute_time=0,
                 crashed=False, has_source_code=False, factory_fn_not_found=False, addr_name_not_found=False,
                 by_new=False,by_create=False,by_create2=False,check_addr_equal=False,check_extcode=False,
                 check_addr0=False):
        self.id: int = id
        self.address: str = address
        self.chain: str = chain
        self.process_start: int = process_start
        self.process_end: int = process_end
        self.execute_time: int = execute_time
        self.crashed: bool = crashed
        self.has_source_code: bool = has_source_code
        self.factory_fn_not_found: bool = factory_fn_not_found
        self.addr_name_not_found:bool=addr_name_not_found
        self.by_new:bool=by_new
        self.by_create:bool=by_create
        self.by_create2:bool=by_create2
        self.check_addr_equal: bool = check_addr_equal
        self.check_extcode: bool = check_extcode
        self.check_addr0: bool = check_addr0

    def convert(self, dictionary: dict):
        for key, value in dictionary.items():
            setattr(self, key, value)
        return self
