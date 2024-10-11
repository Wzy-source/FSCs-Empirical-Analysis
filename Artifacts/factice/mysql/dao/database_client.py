import pymysql
from pymysql.cursors import Cursor

from .address_validation import AddressValidation
from .contract_file import ContractFile
from .contract_relation import ContractRelation
from .implement_contract_validation import ImplementContractValidation
from .potential_metamorphic_contract import PotentialMetamorphicContract
from .sender_in_constructor import SenderInConstructor
from .fsc_validation import FSC_Validation


class DatabaseClient:
    def __init__(self, host=None, port=3306, database=None, user="root", password="123456"):
        self.__host: str = host
        self.__port: int = port
        self.__database: str = database
        self.__user: str = user
        self.__password: str = password
        self.__client: pymysql.Connection = self.__init_client()

    def __del__(self):
        self.close_connect()

    def __init_client(self) -> pymysql.Connection:
        return pymysql.connect(host=self.__host, port=self.__port, database=self.__database,
                               user=self.__user, password=self.__password)

    def __build_dict_by_cursor(self, cursor: Cursor) -> dict:
        desc = cursor.description
        result = cursor.fetchone()
        ret = {}
        if result is None:
            return ret
        for i in range(0, len(desc)):
            name = desc[i][0]
            val = result[i]
            # 这里需要小小的特判一下，pymysql不会把tinyint类型转bool
            if desc[i][1] == 1:
                if val == 1:
                    val = True
                if val == 0:
                    val = False
            ret[name] = val
        return ret

    def __extract_all_from_tuple(self, t: tuple) -> list:
        ret: list = []
        for item in t:
            item_list = list(item)
            ret.append(item_list)
        return ret

    def __extract_id_from_tuple(self, t: tuple) -> list:
        ret: list = []
        for item in t:
            ret.append(item[0])
        return ret

    def is_open(self):
        if self.__client is not None:
            try:
                self.__client.ping(reconnect=False)
                return True
            except Exception:
                return False
        return False

    def open_connect(self):
        self.__client = self.__init_client()

    def close_connect(self):
        if self.is_open():
            self.__client.close()

    def check_connection(self):
        if not self.is_open():
            self.open_connect()

    def save_contract_file(self, contract_file: ContractFile) -> int:
        sql: str = "insert into contract_file (chain,address,name,is_factory,is_created,compiler,balance,txcount," \
                   "create_date,source_code,fixed) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        values: tuple = (contract_file.chain, contract_file.address, contract_file.name, contract_file.is_factory,
                         contract_file.is_created, contract_file.compiler, contract_file.balance, contract_file.txcount,
                         contract_file.create_date, contract_file.source_code, contract_file.fixed)
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, values)
        ret = self.__client.insert_id()
        self.__client.commit()
        return ret

    def save_contract_relation(self, contract_relation: ContractRelation) -> int:
        sql: str = "insert into contract_relation (factory_id,created_id,create_type,tx_hash,gas,gas_used,time_stamp) " \
                   "values (%s,%s,%s,%s,%s,%s,%s)"
        values: tuple = (contract_relation.factory_id, contract_relation.created_id, contract_relation.create_type,
                         contract_relation.tx_hash, contract_relation.gas, contract_relation.gas_used,
                         contract_relation.time_stamp)
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, values)
        ret = self.__client.insert_id()
        self.__client.commit()
        return ret

    def select_contract_file_by_id(self, id: int) -> ContractFile:
        sql: str = "select * from contract_file where id=%s"
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, id)
        self.__client.commit()
        dictionary = self.__build_dict_by_cursor(cursor)
        res = ContractFile()
        return res.convert(dictionary)

    def select_contract_relation_by_id(self, id: int) -> ContractRelation:
        sql: str = "select * from contract_relation where id=%s"
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, id)
        self.__client.commit()
        dictionary = self.__build_dict_by_cursor(cursor)
        res = ContractFile()
        return res.convert(dictionary)

    def select_contract_file_by_chain_and_address(self, chain: str, address: str) -> ContractFile:
        sql: str = "select * from contract_file where chain=%s and address=%s"
        values: tuple = (chain, address)
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, values)
        self.__client.commit()
        dictionary = self.__build_dict_by_cursor(cursor)
        res = ContractFile()
        return res.convert(dictionary)

    def select_contract_relation_by_factory_id_and_created_id(self, factory_id: int,
                                                              created_id: int) -> ContractRelation:
        sql: str = "select * from contract_relation where factory_id=%s and created_id=%s"
        values: tuple = (factory_id, created_id)
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, values)
        self.__client.commit()
        dictionary = self.__build_dict_by_cursor(cursor)
        res = ContractRelation()
        return res.convert(dictionary)

    def select_contract_relation_by_created_id(self, created_id: int) -> ContractRelation:
        sql: str = "select * from contract_relation where created_id=%s"
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, created_id)
        self.__client.commit()
        dictionary = self.__build_dict_by_cursor(cursor)
        res = ContractRelation()
        return res.convert(dictionary)

    def update_contract_file_by_id(self, contract_file: ContractFile):
        sql: str = ("update contract_file set chain=%s,address=%s,name=%s,is_factory=%s,is_created=%s,compiler=%s,"
                    "balance=%s,txcount=%s,create_date=%s,source_code=%s,fixed=%s,is_factory_truth=%s where id = %s")
        values: tuple = (contract_file.chain, contract_file.address, contract_file.name, contract_file.is_factory,
                         contract_file.is_created, contract_file.compiler, contract_file.balance, contract_file.txcount,
                         contract_file.create_date, contract_file.source_code, contract_file.fixed, contract_file.is_factory_truth, contract_file.id)
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, values)
        self.__client.commit()

    def update_contract_relation_by_created_id(self, create_type, created_id):
        sql: str = ("update contract_relation set create_type=%s where created_id=%s")
        values: tuple = (create_type, created_id)
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, values)
        self.__client.commit()

    def select_contract_file_by_contract_type(self, is_factory=None, is_created=None) -> list:
        sql: str = "select id from contract_file where 1=1 "
        values: list = []
        if is_factory is not None:
            sql = sql + " and is_factory=%s "
            values.append(is_factory)
        if is_created is not None:
            sql = sql + " and is_created=%s "
            values.append(is_created)
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, values)
        self.__client.commit()
        res = cursor.fetchall()
        return self.__extract_id_from_tuple(res)

    def select_child_node_id(self, id: int) -> list:
        sql: str = "select created_id from contract_relation where factory_id=%s"
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, id)
        self.__client.commit()
        res = cursor.fetchall()
        return self.__extract_id_from_tuple(res)

    def select_min_id_item_by_id(self, id: int) -> ContractFile:
        sql: str = "select * from contract_file where id>%s order by id limit 1"
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, id)
        self.__client.commit()
        dictionary = self.__build_dict_by_cursor(cursor)
        if len(dictionary) == 0:
            return None
        res = ContractFile()
        return res.convert(dictionary)

    def select_all_contract_relation(self) -> list:
        sql: str = "select factory_id,created_id from contract_relation "
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql)
        self.__client.commit()
        rows = cursor.fetchall()
        factory_and_created_ids = [(row[0], row[1]) for row in rows]
        return factory_and_created_ids

    def select_contract_file_by_chain_and_contract(self, chain: str, is_factory=None, is_created=None, fixed=None) -> list:
        sql: str = "select id from contract_file where chain=%s "
        values: list = [chain]
        if is_factory is not None:
            sql = sql + " and is_factory=%s "
            values.append(is_factory)
        if is_created is not None:
            sql = sql + " and is_created=%s "
            values.append(is_created)
        if fixed is not None:
            sql = sql + " and fixed=%s "
            values.append(fixed)
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, values)
        self.__client.commit()
        res = cursor.fetchall()
        return self.__extract_id_from_tuple(res)

    def select_factories(self) -> list:
        sql: str = "select id from contract_file where is_factory=True "
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql)
        self.__client.commit()
        res = cursor.fetchall()
        return self.__extract_id_from_tuple(res)

    def select_created_date_total_contract_count_by_type(self, is_factory=None, is_created=None) -> list:
        sql_1: str = "select create_date, count(*) " \
                     "from contract_file "
        sql_2: str = "where create_date is not null "
        sql_3: str = "group by create_date ORDER BY STR_TO_DATE(create_date, '%%m/%%d/%%Y')"
        values: list = []
        if is_factory is not None:
            sql_2 = sql_2 + " and is_factory=%s "
            values.append(is_factory)
        if is_created is not None:
            sql_2 = sql_2 + " and is_created=%s "
            values.append(is_created)
        sql = sql_1 + sql_2 + sql_3
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, values)
        self.__client.commit()
        res = cursor.fetchall()
        return self.__extract_all_from_tuple(res)

    def select_factory_total_contract_count(self):
        sql = "select count(*) as factory_num, txcount " \
              "from contract_file " \
              "where is_factory=1 " \
              "group by txcount " \
              "order by txcount"
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql)
        self.__client.commit()
        res = cursor.fetchall()
        return self.__extract_all_from_tuple(res)

    def select_contract_execute_time(self):
        sql = ("select execute_time, count(*) from "
               "(SELECT execute_time FROM address_validation "
               "UNION ALL SELECT execute_time FROM sender_in_constructor) as avetsicet "
               "group by execute_time "
               "order by execute_time")
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql)
        self.__client.commit()
        res = cursor.fetchall()
        return self.__extract_all_from_tuple(res)

    def select_id_by_chain_and_type(self, chain: str, is_factory=None, is_created=None):
        sql: str = ("select min(id) from contract_file where chain=%s and source_code is not null "
                    "and source_code <> '' ")
        values: list = [chain]
        if is_factory is not None:
            sql = sql + " and is_factory=%s "
            values.append(is_factory)
        if is_created is not None:
            sql = sql + " and is_created=%s "
            values.append(is_created)
        sql = sql + " group by source_code"
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, values)
        self.__client.commit()
        res = cursor.fetchall()
        return self.__extract_id_from_tuple(res)

    def select_relation_id_by_factory_id(self, factory_id):
        sql: str = ("select min(id) from contract_relation where factory_id = %s")
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, factory_id)
        self.__client.commit()
        res = cursor.fetchall()
        return self.__extract_id_from_tuple(res)

    def select_metamorphic_contract_by_chain_and_address(self, chain, address):
        sql: str = "select * from potential_metamorphic_contract where chain=%s and address=%s"
        values: tuple = (chain, address)
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, values)
        self.__client.commit()
        dictionary = self.__build_dict_by_cursor(cursor)
        res = PotentialMetamorphicContract()
        return res.convert(dictionary)

    def select_metamorphic_contract_by_id(self, id):
        sql: str = "select * from potential_metamorphic_contract where id=%s"
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, id)
        self.__client.commit()
        dictionary = self.__build_dict_by_cursor(cursor)
        res = PotentialMetamorphicContract()
        return res.convert(dictionary)

    def save_metamorphic_contract(self, contract: PotentialMetamorphicContract):
        sql: str = ("insert into potential_metamorphic_contract (chain,address,create_type,bytecode,decompiled_code,"
                    "dynamic_init_code,implement_setter,implement_getter,pattern1,pattern2) "
                    "values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
        values: tuple = (contract.chain, contract.address, contract.create_type, contract.bytecode,
                         contract.decompiled_code, contract.dynamic_init_code, contract.implement_setter,
                         contract.implement_getter, contract.pattern1, contract.pattern2)
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, values)
        ret = self.__client.insert_id()
        self.__client.commit()
        return ret

    def update_metamorphic_contract_by_id(self, contract: PotentialMetamorphicContract):
        sql: str = (
            "update potential_metamorphic_contract set chain=%s,address=%s,create_type=%s,bytecode=%s,decompiled_code=%s,dynamic_init_code=%s,"
            "implement_setter=%s,implement_getter=%s,pattern1=%s,pattern2=%s where id = %s")
        values: tuple = (contract.chain, contract.address, contract.create_type, contract.bytecode,
                         contract.decompiled_code, contract.dynamic_init_code, contract.implement_setter,
                         contract.implement_getter, contract.pattern1, contract.pattern2, contract.id)
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, values)
        self.__client.commit()

    def select_sender_in_constructor_by_chain_and_address(self, chain, address):
        sql: str = "select * from sender_in_constructor where chain=%s and address=%s"
        values: tuple = (chain, address)
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, values)
        self.__client.commit()
        dictionary = self.__build_dict_by_cursor(cursor)
        res = SenderInConstructor()
        return res.convert(dictionary)

    def select_sender_in_constructor_by_id(self, id):
        sql: str = "select * from sender_in_constructor where id=%s"
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, id)
        self.__client.commit()
        dictionary = self.__build_dict_by_cursor(cursor)
        res = SenderInConstructor()
        return res.convert(dictionary)

    def save_sender_in_constructor(self, constructor: SenderInConstructor):
        sql: str = ("insert into sender_in_constructor (chain,address,process_start,process_end,execute_time,"
                    "crashed,has_source_code,has_issue) "
                    "values (%s,%s,%s,%s,%s,%s,%s,%s)")
        values: tuple = (constructor.chain, constructor.address, constructor.process_start,
                         constructor.process_end, constructor.execute_time, constructor.crashed,
                         constructor.has_source_code, constructor.has_issue)
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, values)
        ret = self.__client.insert_id()
        self.__client.commit()
        return ret

    def save_date_and_type(self, date, create_type):
        sql: str = ("insert into create_date_and_type (date,create_type) values (%s,%s)")
        values: tuple = (date, create_type)
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, values)
        ret = self.__client.insert_id()
        self.__client.commit()
        return ret

    def update_sender_in_constructor_by_id(self, constructor: SenderInConstructor):
        sql: str = (
            "update sender_in_constructor set chain=%s,address=%s,process_start=%s,process_end=%s,"
            "execute_time=%s,crashed=%s,has_source_code=%s,has_issue=%s where id = %s")
        values: tuple = (constructor.chain, constructor.address, constructor.process_start,
                         constructor.process_end, constructor.execute_time, constructor.crashed,
                         constructor.has_source_code, constructor.has_issue, constructor.id)
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, values)
        self.__client.commit()

    def find_max_tx_contract_file(self):
        sql: str = "SELECT id FROM contract_file WHERE contract_file.txcount=10000;"
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql)
        self.__client.commit()
        res = cursor.fetchall()
        return self.__extract_id_from_tuple(res)

    def select_address_validation_by_chain_and_address(self, chain, address):
        sql: str = "select * from address_validation where chain=%s and address=%s"
        values: tuple = (chain, address)
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, values)
        self.__client.commit()
        dictionary = self.__build_dict_by_cursor(cursor)
        res = AddressValidation()
        return res.convert(dictionary)

    def select_address_validation_by_id(self, id):
        sql: str = "select * from address_validation where id=%s"
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, id)
        self.__client.commit()
        dictionary = self.__build_dict_by_cursor(cursor)
        res = AddressValidation()
        return res.convert(dictionary)

    def save_address_validation(self, address_validation: AddressValidation):
        sql: str = ("insert into address_validation (chain,address,process_start,process_end,execute_time,"
                    "crashed,has_source_code,factory_fn_not_found,addr_name_not_found,by_new,by_create,by_create2,"
                    "check_addr_equal,check_extcode,check_addr0 ) "
                    "values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
        values: tuple = (address_validation.chain, address_validation.address, address_validation.process_start,
                         address_validation.process_end, address_validation.execute_time, address_validation.crashed,
                         address_validation.has_source_code, address_validation.factory_fn_not_found,
                         address_validation.addr_name_not_found, address_validation.by_new, address_validation.by_create,
                         address_validation.by_create2, address_validation.check_addr_equal,
                         address_validation.check_extcode, address_validation.check_addr0)
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, values)
        ret = self.__client.insert_id()
        self.__client.commit()
        return ret

    def update_address_validation_by_id(self, address_validation: AddressValidation):
        sql: str = (
            "update address_validation set chain=%s,address=%s,process_start=%s,process_end=%s,execute_time=%s,"
            "crashed=%s,has_source_code=%s,factory_fn_not_found=%s,addr_name_not_found=%s,by_new=%s,by_create=%s,"
            "by_create2=%s,check_addr_equal=%s,check_extcode=%s,check_addr0=%s where id = %s")
        values: tuple = (address_validation.chain, address_validation.address, address_validation.process_start,
                         address_validation.process_end, address_validation.execute_time, address_validation.crashed,
                         address_validation.has_source_code, address_validation.factory_fn_not_found,
                         address_validation.addr_name_not_found, address_validation.by_new, address_validation.by_create,
                         address_validation.by_create2, address_validation.check_addr_equal,
                         address_validation.check_extcode, address_validation.check_addr0, address_validation.id)
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, values)
        self.__client.commit()

    def select_implement_contract_validation_by_chain_and_address(self, chain, address):
        sql: str = "select * from implement_contract_validation where chain=%s and address=%s"
        values: tuple = (chain, address)
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, values)
        self.__client.commit()
        dictionary = self.__build_dict_by_cursor(cursor)
        res = ImplementContractValidation()
        return res.convert(dictionary)

    def select_implement_contract_validation_by_id(self, id):
        sql: str = "select * from implement_contract_validation where id=%s"
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, id)
        self.__client.commit()
        dictionary = self.__build_dict_by_cursor(cursor)
        res = ImplementContractValidation()
        return res.convert(dictionary)

    def save_implement_contract_validation(self, implement_contract_validation: ImplementContractValidation):
        sql: str = ("insert into implement_contract_validation (chain,address,process_start,process_end,execute_time,"
                    "crashed,has_source_code,is_clone_based_factory,not_check,check_addr0,check_is_contract,"
                    "check_fn_call,external_address,internal_address,in_whitelist ) "
                    "values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
        values: tuple = (implement_contract_validation.chain, implement_contract_validation.address,
                         implement_contract_validation.process_start, implement_contract_validation.process_end,
                         implement_contract_validation.execute_time, implement_contract_validation.crashed,
                         implement_contract_validation.has_source_code,
                         implement_contract_validation.is_clone_based_factory,
                         implement_contract_validation.not_check, implement_contract_validation.check_addr0,
                         implement_contract_validation.check_is_contract, implement_contract_validation.check_fn_call,
                         implement_contract_validation.external_address, implement_contract_validation.internal_address,
                         implement_contract_validation.in_whitelist)
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, values)
        ret = self.__client.insert_id()
        self.__client.commit()
        return ret

    def update_implement_contract_validation(self, implement_contract_validation: ImplementContractValidation):
        sql: str = (
            "update implement_contract_validation set chain=%s,address=%s,process_start=%s,process_end=%s,execute_time=%s,"
            "crashed=%s,has_source_code=%s,is_clone_based_factory=%s,not_check=%s,check_addr0=%s,check_is_contract=%s,"
            "check_fn_call=%s,external_address=%s,internal_address=%s,in_whitelist=%s where id = %s")
        values: tuple = (implement_contract_validation.chain, implement_contract_validation.address,
                         implement_contract_validation.process_start, implement_contract_validation.process_end,
                         implement_contract_validation.execute_time, implement_contract_validation.crashed,
                         implement_contract_validation.has_source_code,
                         implement_contract_validation.is_clone_based_factory,
                         implement_contract_validation.not_check, implement_contract_validation.check_addr0,
                         implement_contract_validation.check_is_contract, implement_contract_validation.check_fn_call,
                         implement_contract_validation.external_address, implement_contract_validation.internal_address,
                         implement_contract_validation.in_whitelist, implement_contract_validation.id)
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, values)
        self.__client.commit()

    def select_fsc_validation_by_contract_file_id(self, contract_file_id):
        sql: str = "select * from FSC_Detector_Validation where contract_file_id=%s"
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, contract_file_id)
        self.__client.commit()
        dictionary = self.__build_dict_by_cursor(cursor)
        res = FSC_Validation()
        return res.convert(dictionary)

    def select_all_contract_file_ids(self, chain):
        sql: str = "select id from contract_file where chain = %s"
        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, chain)
        self.__client.commit()
        res = cursor.fetchall()
        return self.__extract_id_from_tuple(res)

    def save_fsc_validation_res(self, validation_res: FSC_Validation):
        sql = ("insert into FSC_Validation (name,address,contain_create_tx,is_factory_detect,contract_file_id,chain,create_tx_hash)"
               "values (%s,%s,%s,%s,%s,%s,%s)")
        values: tuple = (validation_res.name, validation_res.address, validation_res.contain_create_tx, validation_res.is_factory_detect,
                         validation_res.contract_file_id, validation_res.chain, validation_res.create_txhash)

        cursor: Cursor = self.__client.cursor()
        cursor.execute(sql, values)
        ret = self.__client.insert_id()
        self.__client.commit()
        return ret
