import json
import threading
import time

from factice_scripts.utils import _fetch_contract_name_code_compiler
from mysql.api import DatabaseApi, ContractFile
import os


# TODO 后续替换为其他以太坊网络
def save_ethereum_contracts(network, thread_num):
    # 使用相对路径，获取network.json文件
    json_file_path = os.path.join(os.path.dirname(__file__), "..", "contract_data", network + '.json')
    with open(json_file_path, 'r') as f:
        total_lines = sum(1 for line in f)
    part_size = total_lines // thread_num  # 向下取整，剩下的部分暂时忽略
    threads = []
    for i in range(thread_num):
        start_line = i * part_size
        end_line = start_line + part_size
        thread = threading.Thread(target=read_lines_save_contracts,
                                  args=(json_file_path, network, start_line, end_line, i + 1))
        threads.append(thread)
        thread.start()
    # 等待所有线程执行结束
    for thread in threads:
        thread.join()
    print("save ethereum contracts complete!")


def read_lines_save_contracts(json_file_path, chain, start, end, thread_num):
    # 每个线程都与服务器建立一个连接
    db_client = DatabaseApi()
    with open(json_file_path, 'r') as f:
        for i, line in enumerate(f):
            if i < start:
                continue
            if i >= end:
                break
            info = json.loads(line)
            address = info['address']
            cf = db_client.find_contract_file_by_chain_and_address(chain, address)
            if cf.id == -1:  # 当前数据库不存在该合约
                code = ""
                try:
                    _, code, _ = _fetch_contract_name_code_compiler(info['address'], chain)
                except Exception as e:
                    print(f"线程{thread_num}请求源码时出错{e}，进入retry逻辑")
                    retry_num = 1
                    while retry_num <= 5:
                        print(f"线程{thread_num}第{retry_num}次retry")
                        try:
                            time.sleep(2)
                            _, code, _ = _fetch_contract_name_code_compiler(info['address'], chain)
                            break
                        except Exception:
                            retry_num += 1

                if code:
                    db_client.save_contract_file(ContractFile(
                        chain=chain,
                        address=info['address'],
                        name=info['name'],
                        is_factory=False,
                        is_created=False,
                        compiler=info['compiler'],
                        balance=info['balance'],
                        txcount=info['txcount'],
                        create_date=info['date'],
                        source_code=code
                    ))
                    print(f"线程{thread_num}成功保存合约{info['name']}")
                else:
                    print(f"线程{thread_num}依然没有拿到Source_Code,跳过该地址{address}")
            else:
                print(f"线程{thread_num}当前合约{info['name']}已存在，跳过")
            formatted_percentage = "{:.2f}%".format(((i - start) / (end - start)) * 100)
            print(f"线程{thread_num}已处理{i - start}个合约，占比{formatted_percentage}")


if __name__ == '__main__':
    networks = ['mainnet', 'goerli', 'sepolia']
    for network in networks:
        save_ethereum_contracts(network, 16)
