import threading

try:
    from Crypto.Hash import keccak

    sha3 = lambda x: keccak.new(digest_bits=256, data=x).digest()
except:
    import sha3 as _sha3

    sha3 = lambda x: _sha3.sha3_256(x).digest()
from mysql.api import ContractFile, ContractRelation, DatabaseApi, DatabaseClient
from utils import _fetch_binary_code_at_address
from metamorphic.opcodes import CREATE2, CREATE, contain_opcode
import rlp  # version = 0.4.4
from rlp.utils import decode_hex
import binascii
from utils import _fetch_normal_txcount, _fetch_create_date, _fetch_internal_txcount


def get_create_type(network: str, factory_addr: str, created_addr: str) -> str:
    """
    判断标注为create opcode创建的合约到底是通过create创建还是create2创建：
    有以下判断依据：
    1.工厂合约的bytecode包含create，但不包含create2，则一定通过create关键字创建
    2.工厂合约的bytecode包含create2，但不包含create，则一定通过create2关键字创建
    3.工厂合约同时包含两种opcode，通过计算所有可能的create_address
    如果create_address == target_address，则通过create方式创建，如果都不满足，则通过create2创建
    """
    factory_bytecode = _fetch_binary_code_at_address(factory_addr, network)
    contain_create = contain_opcode(factory_bytecode, CREATE)
    contain_create2 = contain_opcode(factory_bytecode, CREATE2)
    if not contain_create and not contain_create2:
        print(f"Factory Contract: {factory_addr} Not Contain CREATE / CREATE2 Opcode")
        return "create"
    if contain_create and not contain_create2:
        return "create"
    if contain_create2 and not contain_create:
        return "create2"
    # 如果工厂合约同时含有create和create2关键字，则进行Hash计算
    print(f"Factory Contract: {factory_addr} Contains CREATE && Create2 Opcode, Calculate All Possible Create Address")
    txcount = _fetch_internal_txcount(factory_addr, network)
    for i in range(1, txcount + 1):
        if created_addr == calculate_create_address(factory_addr, i):
            return "create"
    return "create2"


def calculate_create_address(factory_addr: str, nonce: int) -> str:
    bytes = sha3(rlp.encode([normalize_address(factory_addr), nonce]))[12:]
    addr_str = binascii.hexlify(bytes).decode("ascii")
    return f"0x{addr_str}"


def normalize_address(x, allow_blank=False):
    if allow_blank and x == '':
        return ''
    if len(x) in (42, 50) and x[:2] == '0x':
        x = x[2:]
    if len(x) in (40, 48):
        x = decode_hex(x)
    if len(x) == 24:
        assert len(x) == 24 and sha3(x[:20])[:4] == x[-4:]
        x = x[:20]
    if len(x) != 20:
        raise Exception("Invalid address format: %r" % x)
    return x


def fix(thread_num, network):
    def _handle_one_thread(thread_id, start_idx, end_idx):
        client = DatabaseApi()  # 每个线程保证一个数据库连接
        traverse_num = 0
        for idx in range(start_idx, end_idx):
            traverse_num += 1
            try:
                ctr_file = client.find_contract_file_by_id(all_ids[idx])
                txcount = _fetch_normal_txcount(ctr_file.address, network)
                create_date = _fetch_create_date(ctr_file.address, network)
                if ctr_file.is_created:
                    contract_relation = client.find_contract_relation_by_created_chain_and_address(network,
                                                                                                   ctr_file.address)
                    factory_contract = client.find_contract_file_by_id(contract_relation.factory_id)
                    create_type = get_create_type(network, factory_contract.address, ctr_file.address)
                    # 更新contract_relation文件
                    client.update_contract_relation_type(create_type, ctr_file.id)
                # 更新contract_file文件
                client.save_contract_file(
                    ContractFile(chain=network, address=ctr_file.address,
                                 txcount=txcount, create_date=create_date, fixed=True))
            except Exception as e:
                print(f'{e} 跳过此条')
                continue
            traverse_percentage = "{:.2f}%".format((traverse_num / (end_idx - start_idx)) * 100)
            print(f"thread{thread_id}已修改合约:{ctr_file.id},修改进度为:{traverse_percentage}")
        print(f"Thread{thread_id} Fix Completed!!!")

    db_client = DatabaseApi()
    all_ids = db_client.find_by_contract_chain_and_type(network, 'all', fixed=0)
    part_size = len(all_ids) // thread_num  # 向下取整，剩下的部分暂时忽略
    threads = []
    for i in range(thread_num):
        start_idx = i * part_size
        end_idx = start_idx + part_size
        thread = threading.Thread(target=_handle_one_thread, args=(i + 1, start_idx, end_idx))
        threads.append(thread)
        thread.start()
    end_thread = threading.Thread(target=_handle_one_thread,
                                  args=(thread_num + 1, thread_num * part_size, len(all_ids)))
    threads.append(end_thread)
    end_thread.start()
    # 等待所有线程执行结束
    for thread in threads:
        thread.join()

    print("Fix Complete!")


def fix_is_factory_and_is_created(thread_num):
    def _handle_one_thread(thread_id, start_idx, end_idx):
        traverse_num = 0
        client = DatabaseApi()
        for idx in range(start_idx, end_idx):
            traverse_num += 1
            factory_id, created_id = all_relations[idx]
            factory_file = client.find_contract_file_by_id(factory_id)
            created_file = client.find_contract_file_by_id(created_id)
            client.save_contract_file(ContractFile(
                chain=factory_file.chain,
                address=factory_file.address,
                is_factory=True,
                is_created=factory_file.is_created
            ))
            client.save_contract_file(ContractFile(
                chain=created_file.chain,
                address=created_file.address,
                is_factory=created_file.is_factory,
                is_created=True
            ))
            print(f"线程{thread_id}成功保存factory{factory_id},created{created_id}")
            traverse_percentage = "{:.2f}%".format((traverse_num / (end_idx - start_idx)) * 100)
            print(f"thread{thread_id}修改进度为:{traverse_percentage}")
        print(f"thread{thread_id} fix completed")

    db_client = DatabaseApi()
    all_relations = db_client.get_all_contract_relations()
    part_size = len(all_relations) // thread_num  # 向下取整，剩下的部分暂时忽略
    threads = []
    for i in range(thread_num):
        start_idx = i * part_size
        end_idx = start_idx + part_size
        thread = threading.Thread(target=_handle_one_thread, args=(i + 1, start_idx, end_idx))
        threads.append(thread)
        thread.start()
    end_thread = threading.Thread(target=_handle_one_thread,
                                  args=(thread_num + 1, thread_num * part_size, len(all_relations)))
    threads.append(end_thread)
    end_thread.start()
    # 等待所有线程执行结束
    for thread in threads:
        thread.join()

    print("Fix Complete!")


if __name__ == '__main__':
    fix_is_factory_and_is_created(30)
