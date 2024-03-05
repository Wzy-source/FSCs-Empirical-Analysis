from typing import List, Tuple
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
import datetime
from slither.utils.output import Output
import requests
import os
import shutil
from mysql.api import DatabaseApi, ContractFile, ContractRelation

# 测试地址
create2_factory_addr_test = "0x0000000000FFe8B47B3e2130213B802212439497"
eoa_addr_test = "0x1d1613f0f7c266cEddD192Aa69970Fc536ddda60"
API_KEY = "HPXNN2GP4VFJIBD4USI8QJF6MFI75HRQZT"
Max_TX_NUM = 200


class SCFPreprocessor(AbstractDetector):
    ARGUMENT = 'scf-preprocessor'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.MEDIUM
    HELP = "detect and save factory-related smart contracts"
    WIKI = "https://github.com/crytic/slither/wiki/factory-detect"
    WIKI_TITLE = "Smart Contract Factory Preprocessor"
    WIKI_DESCRIPTION = """
    Detect and save factory-related smart contracts
    """
    WIKI_RECOMMENDATION = """
    None
    """

    def _detect(self) -> List[Output]:
        db_client = DatabaseApi()
        target_address = self.slither.crytic_compile.target
        chain = "mainnet"
        contract_file = db_client.find_contract_file_by_chain_and_address(chain, target_address)
        target_contract = find_target_contract(self.contracts, contract_file.name)
        if target_contract and target_contract.is_factory:
            print(f"{contract_file.name},{target_address}是工厂合约，已更新其contract_type")
            db_client.update_contract_type(chain, target_address, 'factory')
        # factory_addr, txhash = fetch_creator_addr_and_txhash(target_address)
        # # bug：这里的creator一定是外部账户(tx.origin)
        # while not is_eoa_addr(factory_addr):
        #     # 该地址是合约账户，则一定也是factory，可根据txhash判断该父工厂是以什么方式创建子工厂的
        #     txinfo = fetch_internal_txinfo_by_txhash(txhash)
        #     # 根据chain+address，查找creator合约是否存在于数据库中
        #     factory_contract_id = db_client.find_contract_file_by_chain_and_address(chain, factory_addr).id
        #     if factory_contract_id == -1:  # 当合约不存在时，id = -1
        #         print(f"数据库中不存在address={factory_addr}的factory合约，将factory的部分字段保存到数据库中")
        #         factory_name, factory_code, compiler = fetch_contract_name_code_compiler(factory_addr)
        #         if factory_name and factory_code:
        #             print("查找到creator合约源码", factory_name)
        #         else:
        #             print("未找到creator合约源码")
        #         factory_contract_id = db_client.save_contract_file(ContractFile(
        #             chain=chain,
        #             address=factory_addr,
        #             name=factory_name,
        #             compiler=compiler,
        #             source_code=factory_code,
        #             is_factory=True))
        #     # 将合约关系写入关系表，save_contract_relation这个接口会自动的update contract type
        #     db_client.save_contract_relation(ContractRelation(
        #         factory_id=factory_contract_id,
        #         created_id=contract_file.id,
        #         create_type=txinfo['type'],
        #         tx_hash=txhash,
        #         gas=txinfo['gas'],
        #         gas_used=txinfo['gasUsed'],
        #         time_stamp=txinfo['timeStamp']
        #     ))
        #
        #     # 向前迭代地查找creator
        #     factory_addr, txhash = fetch_creator_addr_and_txhash(factory_addr)
        #
        # create_contract_txs = fetch_create_txs(target_address)
        # # 目前最多仅遍历当前工厂合约的Max_TX_NUM个交易
        # for index in range(0, min(len(create_contract_txs), Max_TX_NUM)):
        #     txinfo = create_contract_txs[index]
        #     created_addr = txinfo['contractAddress']  # 创建的合约地址
        #     # 根据chain+address，查找creator合约是否存在于数据库中
        #     created_contract_id = db_client.find_contract_file_by_chain_and_address(chain, created_addr).id
        #     if created_contract_id == -1:
        #         print(f"数据库中不存在created合约，address={created_addr}，将created的部分字段保存到数据库中")
        #         created_name, created_code, compiler = fetch_contract_name_code_compiler(created_addr)
        #         if created_name and created_code:  # 已验证的子合约
        #             print("查找到created合约源码", created_name)
        #         else:
        #             print("未找到created合约源码")
        #         created_contract_id = db_client.save_contract_file(ContractFile(
        #             chain=chain,
        #             address=created_addr,
        #             name=created_name,
        #             is_created=True,
        #             compiler=compiler,
        #             create_date=time_stamp_to_date(txinfo['timeStamp']),
        #             source_code=created_code))
        #     # 将合约关系写入关系表
        #     db_client.save_contract_relation(ContractRelation(
        #         factory_id=contract_file.id,
        #         created_id=created_contract_id,
        #         create_type=txinfo['type'],
        #         tx_hash=txinfo['hash'],
        #         gas=txinfo['gas'],
        #         gas_used=txinfo['gasUsed'],
        #         time_stamp=txinfo['timeStamp']
        #     ))

        return []


"""
Etherscan相关API
"""


def fetch_contract_name_code_compiler(address) -> Tuple[str, str, str]:
    """
    根据智能合约地址获取验证过的合约源代码
    """
    req_url = f"https://api.etherscan.io/api?" \
              f"module=contract&" \
              f"action=getsourcecode&" \
              f"address={address}&" \
              f"apikey={API_KEY}"
    response = requests.get(req_url)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == '1':
            result = data['result'][0]
            # 如果是未验证的合约，返回的source_code和contract_name都为""
            source_code = result['SourceCode']
            contract_name = result['ContractName']
            compiler = result['CompilerVersion'].split("-")[0].replace("v", "")
            return contract_name, source_code, compiler
        else:
            print("API请求失败：", "message", data['message'], "result ", data['result'])
    else:
        print("API请求失败：", 'response.status_code ', response.status_code)


def fetch_creator_addr_and_txhash(address) -> Tuple[str, str]:
    req_url = f"https://api.etherscan.io/api?" \
              f"module=contract&" \
              f"action=getcontractcreation&" \
              f"contractaddresses={address}&" \
              f"apikey={API_KEY}"
    response = requests.get(req_url)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == '1':
            result = data['result'][0]
            creator_addr = result['contractCreator']
            txhash = result['txHash']
            print('creator_addr', creator_addr, 'txhash', txhash)
            return creator_addr, txhash
        else:
            print("API请求失败：", "message", data['message'], "result ", data['result'])
    else:
        print("API请求失败：", 'response.status_code ', response.status_code)


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
                    create_contract_related_txs.append(tx)
            return create_contract_related_txs
        else:
            print("API请求失败：", "message", data['message'], "result ", data['result'])
    else:
        print("API请求失败：", 'response.status_code ', response.status_code)


def fetch_binary_code_at_address(address) -> str:
    req_url = f"https://api.etherscan.io/api?" \
              f"module=proxy&" \
              f"action=eth_getCode&" \
              f"address={address}&" \
              f"tag=latest&" \
              f"apikey={API_KEY}"
    response = requests.get(req_url)
    if response.status_code == 200:
        data = response.json()
        return data['result']
    else:
        print("API请求失败：", 'response.status_code ', response.status_code)


def fetch_internal_txinfo_by_txhash(txhash):
    req_url = f"https://api.etherscan.io/api?" \
              f"module=account&" \
              f"action=txlistinternal&" \
              f"txhash={txhash}&" \
              f"apikey={API_KEY}"
    response = requests.get(req_url)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == '1':
            result = data['result'][0]
            return result
        else:
            print("API请求失败：", "message", data['message'], "result ", data['result'])
    else:
        print("API请求失败：", 'response.status_code ', response.status_code)


"""
文件读写相关方法
"""


def copy_paste_contract_file(source_file_path, destination_folder_path):
    try:
        shutil.copy(source_file_path, destination_folder_path)
        print(f"文件已成功复制到 {destination_folder_path}")
    except Exception as e:
        print(f"复制文件时出错：{e}")


def get_home_folder_path(folder_name) -> str:
    home_directory = os.environ['HOME']
    home_folder_path = os.path.join(home_directory, folder_name)
    os.makedirs(home_folder_path, exist_ok=True)
    return home_folder_path


def save_source_code(file_name, source_code, destination_folder_path):
    # 构建完整的文件路径
    if file_name and source_code:
        file_path = os.path.join(destination_folder_path, file_name)
        # 将源代码写入文件
        with open(file_path, 'w') as file:
            file.write(source_code)
            print(f"合约源代码已保存为 {file_path}")
    else:
        print("file_name或source_code为空")


"""
其他
"""


def find_target_contract(contracts, target_contract_name):
    for contract in contracts:
        if contract.name == target_contract_name:
            return contract
    return None


def is_eoa_addr(address) -> bool:
    # 判断当前地址是否是外部账户地址
    code = fetch_binary_code_at_address(address)
    if code == "0x":
        print(f"{address} 是外部账户地址")
        return True
    else:
        print(f"{address} 是合约账户地址")
        return False


def time_stamp_to_date(time_stamp: str) -> str:
    date = datetime.datetime.fromtimestamp(int(time_stamp))
    formatted_date = date.strftime("%m/%d/%Y").lstrip('0')
    return formatted_date


"""
API请求失败： message NOTOK result  Invalid Address format
"""
