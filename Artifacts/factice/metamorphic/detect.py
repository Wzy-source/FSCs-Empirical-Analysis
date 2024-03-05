import re
from etherscan import fetch_contract_bytecode, fetch_create_txhash, fetch_create_internal_txs
from opcodes import contain_opcode, SELFDESTRUCT, DELEGATECALL, CALLCODE
from contract_node import ContractNode
from typing import Tuple, Optional
from mysql.api import DatabaseApi, ContractFile, ContractRelation, PotentialMetamorphicContract
# from panoramix.decompiler import decompile_bytecode
import threading

meta_addr = "0x00000000e82eb0431756271F0d00CFB143685e7B"


def detect_contract(network, address: str, db_client: DatabaseApi):
    """
    检测address对应的合约是否是一个可变形合约
    1.address and runtime code checking
      ①address格式正确
      ②目标地址是一个合约账户
      ③目标地址的runtime_code包含了污点opcpde
    2.deployment chain construction
    3.metamorphic contract analysis
    4.输出结果：见readme.md
    """
    # address and runtime code checking
    address = address.lower()
    if not is_valid_address(address):
        return
    runtime_code = fetch_contract_bytecode(network, address)  # 获取目标地址的runtime_code
    if (not runtime_code) or (not is_contract_account(runtime_code)):
        db_client.save_metamorphic_contract(PotentialMetamorphicContract(
            address=address,
            chain=network,
        ))
        return
    contain_selfdestruct = contain_opcode(runtime_code, SELFDESTRUCT)
    contain_delegatecall = contain_opcode(runtime_code, DELEGATECALL)
    contain_callcode = contain_opcode(runtime_code, CALLCODE)
    if not (contain_selfdestruct or contain_delegatecall or contain_callcode):
        db_client.save_metamorphic_contract(PotentialMetamorphicContract(
            address=address,
            chain=network,
            bytecode=runtime_code
        ))
        print("Not A Metamorphic Contract: Do Not Contain SELFDESTRUCT / DELEGATECALL / CALLCODE Opcodes")
        return
    # 2.deployment chain construction
    target_node = ContractNode(network, address, runtime_code)
    cur_node = target_node
    while True:
        # 前向查找，先向数据库查找cur_node的factory
        creation = find_factory_addr_and_create_type(network, cur_node.address, db_client)
        if not creation:  # 如果是由EOA部署的合约，creation为None，从而确定deployment chain的起始节点
            break
        factory_addr, create_type = creation
        factory_bytecode = fetch_contract_bytecode(network, cur_node.address)
        factory_node = ContractNode(network, factory_addr, factory_bytecode)
        factory_node.link_succ(create_type, cur_node)
        cur_node = factory_node
    print("Deployment Chain Construct Complete")
    # 3.metamorphic contract analysis
    # cur_node指向起始端factory节点
    # is_pattern1 = detect_metamorphic_pattern1(target_node)
    is_pattern2 = detect_metamorphic_pattern2(target_node)
    db_client.save_metamorphic_contract(PotentialMetamorphicContract(
        address=target_node.address,
        chain=target_node.network,
        create_type=target_node.created_type,
        bytecode=target_node.bytecode,
        pattern2=is_pattern2
    ))
    print("Detect Metamorphic Contract Complete")


def detect_metamorphic_pattern1(target_node: "ContractNode") -> bool:
    """
    第一种变形模式：
    TODO 需要获取到反编译后的代码才能进行分析
    """
    if target_node.created_type == 'create2':
        return True
    return False


def detect_metamorphic_pattern2(target_node: "ContractNode") -> bool:
    """
    第二种变形模式：
    0.cur_node was 'create' created
    1.if cur_node : (self-destruct reachable) and ('create2' created) => True
    2.if cur_node :(not self-destruct reachable) => return False
    3.else return detect(cur_node.prec)
    """
    if target_node.created_type == 'create2':
        return False
    cur_node = target_node.prec
    while cur_node is not None:
        if not (contain_opcode(cur_node.bytecode, SELFDESTRUCT) or
                contain_opcode(cur_node.bytecode, DELEGATECALL)):
            return False
        if cur_node.created_type == 'create2':
            return True
        cur_node = cur_node.prec
    return False


def is_valid_address(address: str) -> bool:
    """
    Check that an address is a valid Ethereum address
    Args:
        address (str): Ethereum address
    Returns:
        bool: Is this address a valid Ethereum address
    """
    regex_match = re.match(r"^0x[a-fA-F0-9]{40}$", address)
    if regex_match is None:
        return False
    return True


def is_contract_account(runtime_code: str) -> bool:
    return runtime_code != "0x"


def find_factory_addr_and_create_type(network: str, created_address: str, db_client: DatabaseApi) -> Optional[
    Tuple[str, str]]:
    """
    先向数据库查找当前合约的factory，如果数据库不存在，则向Etherscan请求，并保存factory合约
    """
    relation = db_client.find_contract_relation_by_created_chain_and_address(network, created_address)
    if relation.id != -1:  # 数据库中存在的情况
        factory_id = relation.factory_id
        create_type = relation.create_type
        factory_address = db_client.find_contract_file_by_id(factory_id).address
        return factory_address, create_type
    # 数据库中不存在的情况
    print(f"数据库中不存在工厂合约关系，created_addr: {created_address}，向Etherscan请求并保存factory合约与合约关系")
    create_txhash = fetch_create_txhash(network, created_address)
    if not create_txhash:
        raise Exception(f"Can Not Fetch Contract Create TxHash: {network, created_address}")
    # 当creator是EOA时，internal tx 为空
    create_internal_txs = fetch_create_internal_txs(network, create_txhash)
    if create_internal_txs:
        for tx in create_internal_txs:
            if (tx.get('type') == 'create' or tx.get('type') == 'create2') and \
                    tx.get('contractAddress') == created_address and tx.get('to') == "":
                factory_address = tx.get('from')
                create_type = tx.get('type')
                print(f"Find Factory Address: {factory_address}, Create Type: {create_type}")
                save_contracts_and_relation(tx, network, db_client, create_txhash)
                return factory_address, create_type
    print(f"Contract: {created_address} Was Created By EOA")
    return None


def find_and_save_contract(network: str, address: str, is_factory: bool, is_created: bool,
                           db_client) -> int:
    ctr_id = db_client.find_contract_file_by_chain_and_address(network, address).id
    if ctr_id == -1:
        ctr_id = db_client.save_contract_file(ContractFile(
            chain=network,
            address=address,
            is_created=is_created,
            is_factory=is_factory))
    return ctr_id


def save_contracts_and_relation(create_tx, network, client, txhash):
    factory_addr = create_tx['from']
    created_addr = create_tx['contractAddress']
    if factory_addr and created_addr:
        fac_id = find_and_save_contract(
            network=network,
            address=factory_addr,
            is_factory=True,
            is_created=False,
            db_client=client
        )
        created_id = find_and_save_contract(
            network=network,
            address=created_addr,
            is_factory=False,
            is_created=True,
            db_client=client
        )
        try:
            # 将合约关系写入关系表
            client.save_contract_relation(ContractRelation(
                factory_id=fac_id,
                created_id=created_id,
                create_type=create_tx['type'],
                tx_hash=txhash,
                gas=create_tx['gas'],
                gas_used=create_tx['gasUsed'],
                time_stamp=create_tx['timeStamp']
            ))
            print(f"已成功写入合约关系：factory:{factory_addr},created:{created_addr}")
        except Exception as e:
            print(f"写入合约关系失败：{e}")


def detect(thread_num: int, network: str):
    def handle_one_thread(thread_id, start_idx, end_idx):
        client = DatabaseApi()
        traverse_num = 0
        for idx in range(start_idx, end_idx):
            created_id = created_ids[idx]
            created_file = client.find_contract_file_by_id(created_id)
            metamorphic_id = client.find_metamorphic_contract_by_chain_and_address(network, created_file.address).id
            if metamorphic_id == -1:
                detect_contract(created_file.chain, created_file.address, client)
            traverse_num += 1
            traverse_percentage = "{:.2f}%".format((traverse_num / (end_idx - start_idx)) * 100)
            print(f"thread{thread_id}已遍历合约：{created_file.address}, 遍历进度为：{traverse_percentage}")
        print(f"Thread{thread_id} Detect Metamorphic Contracts Complete!")

    db_client = DatabaseApi()
    created_ids = db_client.find_by_contract_chain_and_type(network, 'created')
    part_size = len(created_ids) // thread_num  # 向下取整，剩下的部分暂时忽略
    threads = []
    for i in range(thread_num):
        start_idx = i * part_size
        end_idx = start_idx + part_size
        thread = threading.Thread(target=handle_one_thread, args=(i + 1, start_idx, end_idx))
        threads.append(thread)
        thread.start()
    end_thread = threading.Thread(target=handle_one_thread,
                                  args=(thread_num + 1, thread_num * part_size, len(created_ids)))
    threads.append(end_thread)
    end_thread.start()
    # 等待所有线程执行结束
    for thread in threads:
        thread.join()

    print("Detect All Metamorphic Contracts Complete!!!")


if __name__ == '__main__':
    # TODO 先查mainnet的数据集
    detect(8, 'mainnet')
