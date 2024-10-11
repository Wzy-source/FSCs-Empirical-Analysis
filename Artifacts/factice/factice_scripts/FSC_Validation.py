import threading

import requests
import json

from mysql.api import DatabaseApi, ContractFile, FSC_Validation
import re
import subprocess
import os
from api_config import api_keys
import random

API_KEY = "HPXNN2GP4VFJIBD4USI8QJF6MFI75HRQZT"


def fetch_create_txs(factory_address) -> list:
    req_url = f"https://api.etherscan.io/api?" \
              f"module=account&" \
              f"action=txlistinternal&" \
              f"address={factory_address}&" \
              f"sort=desc&" \
              f"apikey={API_KEY}"
    response = requests.get(req_url)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == '1':
            results = data['result']
            create_contract_related_txs = []
            for tx in results:
                # 有些交易是失败的交易，contractAddress字段为空
                if (tx["type"] == "create" or "create2") and tx['contractAddress']:
                    if tx['contractAddress'] != factory_address:
                        create_contract_related_txs.append(tx)
            return create_contract_related_txs
        else:
            print("API请求失败：", "message", data['message'], "result ", data['result'])
    else:
        print("API请求失败：", 'response.status_code ', response.status_code)


def validate_contracts(start, end):
    """
    合约预处理
    依次从数据库中取合约名、编译器版本、源码字符串，保存为临时文件
    设置本地编译器版本
    调用slither进行分析
    直到分析到数据库中最后一个合约为止
    """
    # 统计数据
    db_client = DatabaseApi()
    # 获取数据库首个合约文件
    print(2)
    contract_ids = db_client.select_all_contract_file_ids("mainnet")
    print(len(contract_ids))
    traversed_num = 0
    for contract_idx in range(start, end):
        print(contract_idx)
        contract_id = contract_ids[contract_idx]
        traversed_num += 1
        # 先请求Create Tx
        # 查找当前地址所有交易
        contract_file = db_client.find_contract_file_by_id(contract_id)
        create_txs = fetch_create_txs(contract_file.address)
        contains_create_txs = True if (create_txs is not None) and (len(create_txs) > 0) else False
        first_tx_hash = ""
        if contains_create_txs:
            first_tx_hash = create_txs[0]['hash']

        # 编译前预检查，排除一定不是工厂的可能性，减少因为编译造成的时间消耗
        is_factory_detect = False
        compiler_error = False
        # if not must_not_factory(contract_file.name, contract_file.source_code):
        #     # 设置本地编译器版本,有些版本号可能以"v"开头，将v去除
        #     print(
        #         f"contract name:{contract_file.name} id:{contract_file.id} address:{contract_file.address} 合约可能是factory合约，进行预处理")
        #     set_solc_version(contract_file.compiler)
        #     # 保存一个.sol临时文件到$HOME环境变量下
        #     # 有些合约是后来保存的，可能是未被验证的合约，没有源代码
        #
        #     if contract_file.name and contract_file.source_code and contract_file.address:
        #         project_path = os.path.join(os.environ['HOME'], 'tempcode')
        #         # target_file_name = f"{contract.chain}-{contract.address}-{contract.name}.sol"
        #         # target_file_path = save_temp_project(project_path, target_file_name, contract.source_code)
        #         # 调用slither的scf_preprocessor组件
        #         try:
        #             res = call_scf_preprocessor(contract_file.address, project_path)
        #             if len(res.stdout) == 0:
        #                 compiler_error = True
        #             else:
        #                 is_factory_detect = True if "True" in res.stdout else False
        #                 print(res)
        #         except Exception as e:
        #             print(f"执行detector:scf_preprocessor时出错{e}")
        #         # 删除file_path下的文件
        #         delete_temp_project(project_path)
        # else:
        #     is_factory_detect = False

        # 数据库保存结果
        print(f"contains create_txs:{contains_create_txs}")
        print(f"is factory detect:{is_factory_detect}")
        if not compiler_error:
            db_client.save_fsc_validation_res(FSC_Validation(
                contract_file_id=contract_file.id,
                chain="mainnet",
                address=contract_file.address,
                name=contract_file.name,
                contain_create_tx=contains_create_txs,
                create_tx_hash=first_tx_hash,
                is_factory_detect=is_factory_detect
            ))

        traverse_percentage = "{:.2f}%".format((traversed_num / (end - start)) * 100)
        print(
            f"已遍历合约:{traversed_num},遍历进度约为:{traverse_percentage}")
    print("Contracts Preprocess Complete!")


def delete_temp_project(project_path):
    remove_command = f"rm -rf {project_path}"
    try:
        subprocess.run(remove_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(f'临时项目 {project_path} 已成功删除')
    except Exception as e:
        print(f'删除文件时发生错误：{e}')


def call_scf_preprocessor(address, project_path):
    # 随机选取API_KEY,防止达到请求次数上限
    random_key = api_keys[random.randint(0, len(api_keys) - 1)]
    python_env_path = os.path.join(os.getcwd(), "..", "env/bin/python")
    command = f"{python_env_path} -m slither {address}" \
              f" --etherscan-export-directory {project_path}" \
              f" --etherscan-apikey {random_key}" \
              f" --detect scf-preprocessor"
    print(command)
    return subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def set_solc_version(required_version):
    required_version = required_version.split("+")[0].replace("v", "")
    # commands
    install_command = f"solc-select install {required_version}"
    use_command = f"solc-select use {required_version}"
    # local installed versions
    versions_output = subprocess.check_output(["solc-select", "versions"]).decode("utf-8")
    installed_versions = re.findall(r"\d+\.\d+\.\d+", versions_output)
    # 如果目标版本的solc没有下载，需下载后再指定该版本
    if required_version not in installed_versions:
        print(f"Solidity {required_version} 未在本地下载，需先下载")
        subprocess.run(install_command, shell=True, check=True)
        print(f"Solidity {required_version} 已成功下载")
    subprocess.run(use_command, shell=True, check=True)
    print(f"成功切换到 Solidity {required_version}")


# 基于源码字符串层次的分析
# 1.正则匹配，检查合约字符串中是否存在内联汇编create/create2关键字
# 2.检查是否有new ContractName关键字
def must_not_factory(name, source_code: str) -> bool:
    def must_not_factory_contract(contract_names: list, target_code: str) -> bool:
        create_pattern = r'assembly\s*{[^}]*\b(create|create2)\b[^}]*}'
        create_matches = re.findall(create_pattern, target_code, re.DOTALL)
        if create_matches:
            return False
        for cn in contract_names:
            new_contract_statement = f"new {cn}"
            if new_contract_statement in target_code:
                return False
        return True

    if source_code:
        # 获取所有代码中出现的智能合约的合约名
        maybe_contract_names = []
        new_contract_pattern = r'contract\s+([^\s{]+)\s*{'
        new_contract_matches = re.findall(new_contract_pattern, source_code, re.DOTALL)
        for match in new_contract_matches:
            maybe_contract_names.append(match)
        if source_code.startswith("{{"):
            # standard_json形式:只看main contract
            info: dict = json.loads(source_code[1:-1])
            language, sources = info['language'], info['sources']
            if language == 'Solidity':
                for file_path, file, in sources.items():
                    if not must_not_factory_contract(maybe_contract_names, file['content']):
                        return False
            return True
        else:  # 无依赖合约形式
            return must_not_factory_contract(maybe_contract_names, source_code)
    else:
        return True


if __name__ == '__main__':
    client = DatabaseApi()
    total_test_contract_num = 10000
    thread_num = 8
    part_size = total_test_contract_num // thread_num  # 向下取整，剩下的部分暂时忽略
    threads = []
    for i in range(8):
        start_idx = i * part_size
        end_idx = start_idx + part_size
        thread = threading.Thread(target=validate_contracts, args=(start_idx, end_idx))
        threads.append(thread)
        thread.start()
    end_thread = threading.Thread(target=validate_contracts,
                                  args=(thread_num * part_size, total_test_contract_num))
    threads.append(end_thread)
    end_thread.start()
    # 等待所有线程执行结束
    for thread in threads:
        thread.join()
    print("Complete!!!")
    # validate_contracts()
