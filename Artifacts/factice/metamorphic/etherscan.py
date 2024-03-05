import random
import requests
import time
from typing import Optional, Tuple, List, Dict

urls = {
    "mainnet": "api.etherscan.io",
    "goerli": "api-goerli.etherscan.io",
    "kovan": "api-kovan.etherscan.io",
    "rinkeby": "api-rinkeby.etherscan.io",
    "ropsten": "api-ropsten.etherscan.io",
    "sepolia": "api-sepolia.etherscan.io",
}

api_keys = [
    "15F6V2ZIN6FPNW2RAHZ6RX9R18IAIK5QJQ",
    "HPXNN2GP4VFJIBD4USI8QJF6MFI75HRQZT",
    "IITPA3E4JGAUSJ8ZFT24CE3E3NV7RFR4WN",
    "3H114IUEUJTJ63HNGWXF9QNQX5CDSPSF5U",
    "ZI6U81UW4CBKN9VH1VN39MJWP6RDABG36E",
    "MXCXU56KHGZTRG95U3CAZXANZPTSTTPJNV",
    "91I49MJVPJM8R1PV839ERTIFGZYS7RIKYV",
    "G3SSR6UJ67C9FTI41W5STF77K1Q2NUBUGN",
    "A7ZF1UYT2RF8RE8JHBPYUHE2M8AEHEMSJW",
    "CZTEI2RWPMFIKC7K13Z6YT2NIN1ZWJQ8MU",
    "VVYKRJJQQNTWZQ57Q1IQG3UB23IJW5XJ85",
    "H4IFNKVMV134J8WRZ9KAJEA8DJ2BSR4HWF"
]


def random_key() -> str:
    return api_keys[random.randint(0, len(api_keys) - 1)]


# TODO 判断返回的是creation_code还是runtime_code?
def fetch_contract_bytecode(network: str, address: str) -> Optional[str]:
    req_url = f"https://" \
              f"{urls[network]}" \
              f"/api?" \
              f"module=proxy&" \
              f"action=eth_getCode&" \
              f"address={address}&" \
              f"tag=latest&" \
              f"apikey={random_key()}"
    for i in range(5):
        try:
            response = requests.get(req_url)
        except Exception as e:
            print(f"请求失败{e}，进入重试逻辑")
        else:
            time.sleep(0.1)
            break
    if response.status_code == 200:
        data = response.json()
        return data['result']
    else:
        print("API请求失败：", 'response.status_code ', response.status_code)
    return None


def fetch_contract_name_code_compiler(network, address: str) -> Optional[Tuple[str, str, str]]:
    """
    根据智能合约地址获取验证过的合约源代码
    """
    req_url = f"https://" \
              f"{urls[network]}" \
              f"/api?" \
              f"module=contract&" \
              f"action=getsourcecode&" \
              f"address={address}&" \
              f"apikey={random_key()}"
    for i in range(5):
        try:
            response = requests.get(req_url)
        except Exception as e:
            print(f"请求失败{e}，进入重试逻辑")
        else:
            time.sleep(0.1)
            break
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
            print("API请求失败：", "message: ", data['message'], "result: ", data['result'])
    else:
        print("API请求失败：", 'response.status_code ', response.status_code)
    return None


def fetch_create_txhash(network: str, address: str) -> Optional[str]:
    req_url = f"https://" \
              f"{urls[network]}" \
              f"/api?" \
              f"module=contract&" \
              f"action=getcontractcreation&" \
              f"contractaddresses={address}&" \
              f"apikey={random_key()}"
    for i in range(5):
        try:
            response = requests.get(req_url)
        except Exception as e:
            print(f"请求失败{e}，进入重试逻辑")
        else:
            time.sleep(0.1)
            break
    if response.status_code == 200:
        data = response.json()
        if data['status'] == '1':
            result = data['result'][0]
            txhash = result['txHash']
            return txhash
        else:
            print("API请求失败：", "message: ", data['message'], "result: ", data['result'])
    else:
        print("API请求失败：", 'response.status_code ', response.status_code)


def fetch_create_internal_txs(network: str, txhash: str) -> Optional[List[Dict]]:
    req_url = f"https://" \
              f"{urls[network]}" \
              f"/api?" \
              f"module=account&" \
              f"action=txlistinternal&" \
              f"txhash={txhash}&" \
              f"apikey={random_key()}"
    for i in range(5):
        try:
            response = requests.get(req_url)
        except Exception as e:
            print(f"请求失败{e}，进入重试逻辑")
        else:
            time.sleep(0.1)
            break
    if response.status_code == 200:
        data = response.json()
        if data['status'] == '1':
            return data['result']
        else:
            # 若当前账户不存在internal交易时，进入此逻辑
            print("API请求失败：", "message: ", data['message'], "result: ", data['result'])
    else:
        print("API请求失败：", 'response.status_code ', response.status_code)
