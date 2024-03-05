import threading
import time

from mysql.api import DatabaseApi, ContractFile
from utils import _fetch_normal_txcount


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
                txcount=factory_file.txcount,
                is_created=factory_file.is_created,
                fixed=True
            ))
            client.save_contract_file(ContractFile(
                chain=created_file.chain,
                address=created_file.address,
                txcount=created_file.txcount,
                is_factory=created_file.is_factory,
                is_created=True,
                fixed=True
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


# fix==2
def fix_factory_created_tx_count(network, thread_num):
    def _handle_one_thread(thread_id, start_idx, end_idx):
        traverse_num = 0
        client = DatabaseApi()
        for idx in range(end_idx, start_idx, -1):
            traverse_num += 1
            fac_id = created_ids[idx]
            fac_file = client.find_contract_file_by_id(fac_id)
            if fac_file.txcount == 0:
                # 获取实际的txcount
                txcount = _fetch_normal_txcount(fac_file.address, network)
                if txcount != 0:
                    fac_file.txcount = txcount
                    client.save_contract_file(fac_file)
                    print(f"thread{thread_id}成功修改txcount，id:{fac_file.id}")
            traverse_percentage = "{:.2f}%".format((traverse_num / (end_idx - start_idx)) * 100)
            print(f"thread{thread_id, network}修改进度为:{traverse_percentage}")
        print(f"thread{thread_id} fix completed")

    db_client = DatabaseApi()
    # 先处理factory
    # fac_ids = db_client.find_by_contract_chain_and_type(network, 'factory')
    created_ids = db_client.find_by_contract_chain_and_type(network, 'created')
    part_size = len(created_ids) // thread_num  # 向下取整，剩下的部分暂时忽略
    threads = []
    for i in range(thread_num):
        start_idx = i * part_size
        end_idx = start_idx + part_size
        thread = threading.Thread(target=_handle_one_thread, args=(i + 1, start_idx, end_idx))
        threads.append(thread)
        thread.start()
    end_thread = threading.Thread(target=_handle_one_thread,
                                  args=(thread_num + 1, thread_num * part_size, len(created_ids)))
    threads.append(end_thread)
    end_thread.start()
    # 等待所有线程执行结束
    for thread in threads:
        thread.join()

    print("Fix Complete!")


if __name__ == '__main__':
    # fix_is_factory_and_is_created(30)
    networks = ['goerli', 'mainnet', 'sepolia']
    for network in networks:
        fix_factory_created_tx_count(network, 12)
