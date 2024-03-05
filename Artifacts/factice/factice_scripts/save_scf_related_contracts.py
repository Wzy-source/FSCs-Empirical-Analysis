import threading

from utils import _fetch_create_txs, _fetch_contract_name_code_compiler, _time_stamp_to_date, \
    _fetch_create_txs_by_txhash, _fetch_create_txhash
from mysql.api import DatabaseApi, ContractFile, ContractRelation


# 56855个created合约
# 5254个factory合约
# 保存与SCF相关的智能合约

def _find_and_save_contract(network: str, address: str, is_factory: bool, is_created: bool,
                            db_client=None) -> int:
    ctr_id = db_client.find_contract_file_by_chain_and_address(network, address).id
    if ctr_id == -1:
        print(f"数据库中不存在该合约，address={address}，将该的部分字段保存到数据库中")
        ctr_info = _fetch_contract_name_code_compiler(address, network=network)
        name, code, compiler = None, None, None
        if not ctr_info:
            print(f"未找到当前合约源码，network={network},address={address}")
        else:
            name, code, compiler = ctr_info

        ctr_id = db_client.save_contract_file(ContractFile(
            chain=network,
            address=address,
            name=name,
            is_created=is_created,
            is_factory=is_factory,
            compiler=compiler,
            source_code=code))
        print("成功保存合约源码")
    else:
        print(f"数据库中已经存在该合约，address={address}")
    return ctr_id


def _handle_one_create_tx(create_tx, network, client, txhash) -> bool:
    factory_addr = create_tx['from']
    created_addr = create_tx['contractAddress']
    if factory_addr and created_addr:
        fac_id = _find_and_save_contract(
            network=network,
            address=factory_addr,
            is_factory=True,
            is_created=False,
            db_client=client
        )
        created_id = _find_and_save_contract(
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
            return True
        except Exception as e:
            print(f"写入合约关系失败：{e}")
            return False
    else:
        print("create_tx的From字段为空!!!")
        return False


def save_all_factory_contracts(thread_num, network):
    """
    步骤2.2 保存所有工厂合约：
    S1:找所有factory & normal合约的create_txhash
    S2:根据create_txhash获取到internal_txs，过滤，仅返回与create相关的internal_txs
    S3:根据internal_tx的from字段，反推得到对应的工厂合约
    """

    def _handle_one_thread(thread_id, start_idx, end_idx):
        client = DatabaseApi()  # 每个线程保证一个数据库连接
        traverse_num = 0
        for idx in range(start_idx, end_idx):
            traverse_num += 1
            ctr_file = client.find_contract_file_by_id(all_ids[idx])
            create_txhash = _fetch_create_txhash(ctr_file.address, network)
            # _fetch_create_txs_by_txhash中的返回值不包含tx_hash
            create_txs = _fetch_create_txs_by_txhash(create_txhash, network)
            if create_txs and len(create_txs) > 0:
                for create_tx in create_txs:
                    success = _handle_one_create_tx(create_tx, network, client, create_txhash)
                    print(f"交易{create_txhash}处理{'成功' if success else '失败'}")

            traverse_percentage = "{:.2f}%".format((traverse_num / (end_idx - start_idx)) * 100)
            print(f"thread{thread_id}已遍历合约:{ctr_file.id},遍历进度为:{traverse_percentage}")
        print(f"Thread{thread_id} Save All Factory Contracts Completed!!!")

    # 获取并保存合约

    db_client = DatabaseApi()
    all_ids = db_client.find_by_contract_chain_and_type(network, 'all')
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

    print("Save All Factory Contracts Complete!")


def save_all_created_contracts(thread_num, network):
    """
    步骤2.3 保存所有created合约
    """

    def _handle_one_thread(thread_id, start_idx, end_idx):
        client = DatabaseApi()  # 每个线程保证一个数据库连接
        traverse_num = 0
        for idx in range(start_idx, end_idx):
            traverse_num += 1
            ctr_id = all_ids[idx]
            ctr_file: ContractFile = client.find_contract_file_by_id(ctr_id)
            ctx_addr = ctr_file.address
            # _fetch_create_txs返回的字段中包含hash字段
            create_txs = _fetch_create_txs(ctx_addr)
            if create_txs and len(create_txs) > 0:
                if len(create_txs) > 100:
                    create_txs = create_txs[:100]
                for create_tx in create_txs:
                    success = _handle_one_create_tx(create_tx, network, client, create_tx['hash'])
                    print(f"交易{create_tx['hash']}处理{'成功' if success else '失败'}")

            traverse_percentage = "{:.2f}%".format((traverse_num / (end_idx - start_idx)) * 100)
            print(f"thread{thread_id}已遍历合约:{ctr_file.id},遍历进度为:{traverse_percentage}")
        print(f"Thread{thread_id} Save All Created Contracts Completed!!!")

    db_client = DatabaseApi()
    all_ids = db_client.find_by_contract_chain_and_type(network, 'all')
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

    print("Save All Created Contracts Complete!")


if __name__ == '__main__':
    # networks = ['mainnet', 'goerli', 'sepolia']
    # for network in networks:
    #     save_all_factory_contracts(16, network)
    address = "0x5a291bbbb5b138601f1f217922b57057de628b4b"
    client = DatabaseApi()
    id = _find_and_save_contract(network='mainnet', address=address, is_factory=True, is_created=False,
                                 db_client=DatabaseApi())
    print(id)
