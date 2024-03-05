from .contract_file_node import ContractFileNode
from .dao.address_validation import AddressValidation
from .dao.contract_file import ContractFile
from .dao.contract_relation import ContractRelation
from .dao.database_client import DatabaseClient
from .dao.implement_contract_validation import ImplementContractValidation
from .dao.potential_metamorphic_contract import PotentialMetamorphicContract
from typing import List, Tuple
from .dao.sender_in_constructor import SenderInConstructor

# database
FACTICE_DATA = "factice_data"
SMART_CONTRACT = "smart_contract"
SMART_CONTRACT_TEST = "smart_contract_test"


class DatabaseApi:
    def __init__(self):
        self.__databaseClient: DatabaseClient = DatabaseClient(host="114.212.247.243", database=FACTICE_DATA)

    '''
    保存一个合约文件，参数为一个合约实体，按合约实体的参数填满即可
    '''

    def save_contract_file(self, contract_file: ContractFile) -> int:
        self.__databaseClient.check_connection()
        # 统一将字符转为小写形式
        contract_file.address = contract_file.address.lower()
        contract_file_in = self.__databaseClient.select_contract_file_by_chain_and_address(
            contract_file.chain, contract_file.address)
        if contract_file_in.id == -1:
            return self.__databaseClient.save_contract_file(contract_file)
        else:
            for key, val in contract_file.__dict__.items():
                if val is not None and key != 'id':
                    setattr(contract_file_in, key, val)
            self.__databaseClient.update_contract_file_by_id(contract_file_in)
            return contract_file_in.id

    def save_date_type(self, date, create_type):
        self.__databaseClient.check_connection()
        self.__databaseClient.save_date_and_type(date, create_type)

    '''
    保存一个合约关系，参数为一个关系实体，填写完相应的参数即可
    '''

    def save_contract_relation(self, contract_relation: ContractRelation) -> int:
        self.__databaseClient.check_connection()

        if contract_relation.factory_id == contract_relation.created_id:
            raise Exception(f'factory_id和created_id不允许相同,factory_id{contract_relation.factory_id}')

        contract_relation_in: ContractRelation = self.__databaseClient.select_contract_relation_by_factory_id_and_created_id(
            contract_relation.factory_id, contract_relation.created_id)
        if contract_relation_in.id != -1:
            return contract_relation_in.id

        factory: ContractFile = self.__databaseClient.select_contract_file_by_id(contract_relation.factory_id)
        factory.is_factory = True
        self.__databaseClient.update_contract_file_by_id(factory)

        created: ContractFile = self.__databaseClient.select_contract_file_by_id(contract_relation.created_id)
        created.is_created = True
        self.__databaseClient.update_contract_file_by_id(created)

        return self.__databaseClient.save_contract_relation(contract_relation)

    '''
    根据created_id查找factory-created 合约关系
    '''

    def find_contract_relation_by_created_chain_and_address(self, chain: str, address: str) -> ContractRelation:
        self.__databaseClient.check_connection()
        address = address.lower()
        created: ContractFile = self.__databaseClient.select_contract_file_by_chain_and_address(chain, address)
        return self.__databaseClient.select_contract_relation_by_created_id(created.id)

    '''
    根据id查合约详细信息
    '''

    def find_contract_file_by_id(self, id: int) -> ContractFile:
        self.__databaseClient.check_connection()
        return self.__databaseClient.select_contract_file_by_id(id)

    def find_contract_relation_by_id(self, id: int) -> ContractRelation:
        self.__databaseClient.check_connection()
        return self.__databaseClient.select_contract_relation_by_id(id)

    def select_relation_id_by_factory_id(self, id: int):
        self.__databaseClient.check_connection()
        return self.__databaseClient.select_relation_id_by_factory_id(id)

    """
    根据chain+address查合约详细信息
    """

    def find_contract_file_by_chain_and_address(self, chain: str, address: str) -> ContractFile:
        self.__databaseClient.check_connection()
        address = address.lower()
        return self.__databaseClient.select_contract_file_by_chain_and_address(chain, address)

    '''
    更新合约类型，参数chain和address用于指定唯一一个合约，contract_type可选值:factory,created,normal
    填写factory会将合约改成factory类型，填写created会将合约改成created类型
    此处可以调用两次，分别将同一个合约设置成既是factory类型又是created类型  
    '''

    def update_contract_type(self, chain: str, address: str, contract_type: str):
        self.__databaseClient.check_connection()
        address = address.lower()
        contract_file: ContractFile = self.__databaseClient.select_contract_file_by_chain_and_address(chain, address)
        if contract_type == "factory":
            contract_file.is_factory = True
        if contract_type == "created":
            contract_file.is_created = True
        if contract_type == "normal":
            contract_file.is_factory = False
            contract_file.is_created = False
        self.__databaseClient.update_contract_file_by_id(contract_file)

    def update_contract_relation_type(self, create_type, created_id):
        self.__databaseClient.check_connection()
        self.__databaseClient.update_contract_relation_by_created_id(create_type, created_id)

    '''
    根据合约类型查所有符合该类型的合约id
    '''

    def find_by_contract_type(self, contract_type: str) -> list:
        self.__databaseClient.check_connection()
        res = []
        if contract_type == "factory":
            res = self.__databaseClient.select_contract_file_by_contract_type(is_factory=True)
        if contract_type == "created":
            res = self.__databaseClient.select_contract_file_by_contract_type(is_created=True)
        if contract_type == "normal":
            res = self.__databaseClient.select_contract_file_by_contract_type(is_factory=False, is_created=False)
        return res

    '''
    构建合约树，不包含合约具体内容
    '''

    def build_contract_file_tree(self, id: int) -> ContractFileNode:
        self.__databaseClient.check_connection()
        contract_file: ContractFile = self.__databaseClient.select_contract_file_by_id(id)
        contract_file_node = ContractFileNode(contract_file=contract_file)

        sub_id_list: list = self.__databaseClient.select_child_node_id(id)
        if len(sub_id_list) != 0:
            for sub_id in sub_id_list:
                contract_file_node.children.append(self.build_contract_file_tree(sub_id))
        return contract_file_node

    '''
    传入id，寻找下一个id的合约返回，当返回值为None时，说明遍历完毕
    使用时，第一次传入0，后面每次调用时传入前一个结果的id即可，当返回值为None，跳出循环
    '''

    def traversal_contract_file(self, id: int = 0) -> ContractFile:
        self.__databaseClient.check_connection()
        if id is None:
            id = 0
        return self.__databaseClient.select_min_id_item_by_id(id)

    """
    规定chain + type
    返回具有unique source code的合约id
    """

    def find_id_by_chain_and_contract_type(self, chain: str, contract_type: str) -> list:
        self.__databaseClient.check_connection()
        res = []
        if contract_type == "factory":
            res = self.__databaseClient.select_id_by_chain_and_type(chain=chain, is_factory=True)
        if contract_type == "created":
            res = self.__databaseClient.select_id_by_chain_and_type(chain=chain, is_created=True)
        if contract_type == "normal":
            res = self.__databaseClient.select_id_by_chain_and_type(chain=chain, is_factory=False, is_created=False)
        return res

    def get_all_contract_relations(self) -> List[Tuple[int, int]]:
        self.__databaseClient.check_connection()
        return self.__databaseClient.select_all_contract_relation()

    def select_factories(self):
        self.__databaseClient.check_connection()
        return self.__databaseClient.select_factories()

    def find_by_contract_chain_and_type(self, chain: str, contract_type: str, fixed=None) -> list:
        self.__databaseClient.check_connection()
        res = []
        if contract_type == "all":
            res = self.__databaseClient.select_contract_file_by_chain_and_contract(chain=chain, fixed=fixed)
        if contract_type == "factory":
            res = self.__databaseClient.select_contract_file_by_chain_and_contract(chain=chain, is_factory=True,
                                                                                   fixed=fixed)
        if contract_type == "created":
            res = self.__databaseClient.select_contract_file_by_chain_and_contract(chain=chain, is_created=True,
                                                                                   fixed=fixed)
        if contract_type == "normal":
            res = self.__databaseClient.select_contract_file_by_chain_and_contract(chain=chain, is_factory=False,
                                                                                   is_created=False, fixed=fixed)
        return res

    def find_create_date_total_contract_count_by_type(self, contract_type: str):
        """获取每天新增的合约数"""
        self.__databaseClient.check_connection()
        res = []
        if contract_type == "all":
            res = self.__databaseClient.select_created_date_total_contract_count_by_type()
        if contract_type == "factory":
            res = self.__databaseClient.select_created_date_total_contract_count_by_type(is_factory=True)
        if contract_type == "created":
            res = self.__databaseClient.select_created_date_total_contract_count_by_type(is_created=True)
        if contract_type == "normal":
            res = self.__databaseClient.select_created_date_total_contract_count_by_type(is_factory=False,
                                                                                         is_created=False)
        return res

    def find_factory_num_and_txcont(self):
        """获取工厂合约数对应的交易数"""
        self.__databaseClient.check_connection()
        res = self.__databaseClient.select_factory_total_contract_count()
        return res

    def find_contract_execute_time(self):
        """获取合约的执行时间"""
        self.__databaseClient.check_connection()
        res = self.__databaseClient.select_contract_execute_time()
        return res

    def save_metamorphic_contract(self, contract: PotentialMetamorphicContract) -> int:
        self.__databaseClient.check_connection()
        # 统一将字符转为小写形式
        contract.address = contract.address.lower()
        metamorphic_contract_in = self.__databaseClient.select_metamorphic_contract_by_chain_and_address(
            contract.chain, contract.address)
        if metamorphic_contract_in.id == -1:
            return self.__databaseClient.save_metamorphic_contract(contract)
        else:
            for key, val in contract.__dict__.items():
                if val is not None and key != 'id':
                    setattr(metamorphic_contract_in, key, val)
            self.__databaseClient.update_metamorphic_contract_by_id(metamorphic_contract_in)
            return metamorphic_contract_in.id

    def find_metamorphic_contract_by_chain_and_address(self, chain: str, address: str) -> PotentialMetamorphicContract:
        self.__databaseClient.check_connection()
        address = address.lower()
        return self.__databaseClient.select_metamorphic_contract_by_chain_and_address(chain, address)

    def save_sender_in_constructor(self, constructor: SenderInConstructor) -> int:
        self.__databaseClient.check_connection()
        # 统一将字符转为小写形式
        constructor.address = constructor.address.lower()
        constructor_in = self.__databaseClient.select_sender_in_constructor_by_chain_and_address(
            constructor.chain, constructor.address)
        if constructor_in.id == -1:
            return self.__databaseClient.save_sender_in_constructor(constructor)
        else:
            for key, val in constructor.__dict__.items():
                if val is not None and key != 'id':
                    setattr(constructor_in, key, val)
            self.__databaseClient.update_sender_in_constructor_by_id(constructor_in)
            return constructor_in.id

    def find_sender_in_constructor_by_chain_and_address(self, chain: str, address: str) -> SenderInConstructor:
        self.__databaseClient.check_connection()
        address = address.lower()
        return self.__databaseClient.select_sender_in_constructor_by_chain_and_address(chain, address)

    def find_max_tx_contracts(self) -> list:
        self.__databaseClient.check_connection()
        return self.__databaseClient.find_max_tx_contract_file()

    def save_address_validation(self, address_validation: AddressValidation) -> int:
        self.__databaseClient.check_connection()
        # 统一将字符转为小写形式
        address_validation.address = address_validation.address.lower()
        address_validation_in = self.__databaseClient.select_address_validation_by_chain_and_address(
            address_validation.chain, address_validation.address)
        if address_validation_in.id == -1:
            return self.__databaseClient.save_address_validation(address_validation)
        else:
            for key, val in address_validation.__dict__.items():
                if val is not None and key != 'id':
                    setattr(address_validation_in, key, val)
            self.__databaseClient.update_address_validation_by_id(address_validation_in)
            return address_validation_in.id

    def find_address_validation_by_chain_and_address(self, chain: str, address: str) -> AddressValidation:
        self.__databaseClient.check_connection()
        address = address.lower()
        return self.__databaseClient.select_address_validation_by_chain_and_address(chain, address)

    def save_implement_contract_validation(self, implement_contract_validation: ImplementContractValidation) -> int:
        self.__databaseClient.check_connection()
        # 统一将字符转为小写形式
        implement_contract_validation.address = implement_contract_validation.address.lower()
        implement_contract_validation_in = self.__databaseClient.select_implement_contract_validation_by_chain_and_address(
            implement_contract_validation.chain, implement_contract_validation.address)
        if implement_contract_validation_in.id == -1:
            return self.__databaseClient.save_implement_contract_validation(implement_contract_validation)
        else:
            for key, val in implement_contract_validation.__dict__.items():
                if val is not None and key != 'id':
                    setattr(implement_contract_validation_in, key, val)
            self.__databaseClient.update_implement_contract_validation(implement_contract_validation_in)
            return implement_contract_validation_in.id

    def find_implement_contract_validation_by_chain_and_address(self, chain: str, address: str) -> ImplementContractValidation:
        self.__databaseClient.check_connection()
        address = address.lower()
        return self.__databaseClient.select_implement_contract_validation_by_chain_and_address(chain, address)
