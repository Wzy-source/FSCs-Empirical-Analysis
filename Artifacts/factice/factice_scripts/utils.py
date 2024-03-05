import time
from typing import Tuple
from api_config import random_key, urls
import requests
import datetime
import json
import os


def _data_preprocessing(network):
    """去掉json文件中的无效行"""
    original_path = os.path.join(os.path.dirname(__file__), "..", "contract_data", network + '_raw.json')
    filtered_path = os.path.join(os.path.dirname(__file__), "..", "contract_data", network + '.json')
    if os.path.exists(filtered_path):
        return
    with open(original_path, 'r') as input_file, open(filtered_path, 'w') as output_file:
        for line in input_file:
            try:
                # 解析 JSON 对象
                data = json.loads(line)
                # 判断是否包含 'address' 字段
                if 'address' in data:
                    # 写包含 'address' 字段的行到新文件
                    output_file.write(line)
            except json.JSONDecodeError:
                # 忽略无效的 JSON 行
                pass


def _create_proxies(ip, port):
    """使用代理"""
    proxies = {
        "http": f"http://{ip}:{port}",
        "https": f"http://{ip}:{port}"
    }
    return proxies


def _fetch_create_txs(factory_address, network='mainnet') -> list:
    req_url = f"https://" \
              f"{urls[network]}" \
              f"/api?" \
              f"module=account&" \
              f"action=txlistinternal&" \
              f"address={factory_address}&" \
              f"sort=desc&" \
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
            results = data['result']
            create_contract_related_txs = []
            for tx in results:
                # 有些交易是失败的交易，contractAddress字段为空
                print(f"当前交易类型{tx['type']}")
                if (tx["type"] == "create" or "create2") and tx['contractAddress']:
                    create_contract_related_txs.append(tx)
            return create_contract_related_txs
        else:
            print("API请求失败：", "message: ", data['message'], "result: ", data['result'])
    else:
        print("API请求失败：", 'response.status_code ', response.status_code)


def _is_eoa_addr(address) -> bool:
    # 判断当前地址是否是外部账户地址
    code = _fetch_binary_code_at_address(address)
    if code == "0x":
        print(f"{address} 是外部账户地址")
        return True
    else:
        print(f"{address} 是合约账户地址")
        return False


def _time_stamp_to_date(time_stamp: str) -> str:
    date = datetime.datetime.fromtimestamp(int(time_stamp))
    formatted_date = date.strftime("%m/%d/%Y").lstrip('0')
    return formatted_date


def _fetch_contract_name_code_compiler(address, network='mainnet') -> Tuple[str, str, str]:
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


def _fetch_binary_code_at_address(address, network='mainnet') -> str:
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


def _fetch_internal_txinfo_by_txhash(txhash: str, network='mainnet') -> list:
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
            result = data['result']
            return result
        else:
            print("API请求失败：", "message: ", data['message'], "result: ", data['result'])
    else:
        print("API请求失败：", 'response.status_code ', response.status_code)


def _fetch_create_txhash(address, network='mainnet') -> str:
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


def _fetch_create_txs_by_txhash(txhash, network='mainnet') -> list:
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
            return list(filter(lambda x: x["type"] == 'create' or x["type"] == 'create2', data['result']))
        else:
            print("API请求失败：", "message: ", data['message'], "result: ", data['result'])
    else:
        print("API请求失败：", 'response.status_code ', response.status_code)


def _fetch_internal_txcount(address, network='mainnet'):
    """获取账户交易数"""
    req_url = f"https://" \
              f"{urls[network]}" \
              f"/api?" \
              f"module=proxy&" \
              f"action=eth_getTransactionCount&" \
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
        return int(data['result'], 16)
    else:
        print("API请求失败：", 'response.status_code ', response.status_code)
    raise Exception('网络错误!')


def _fetch_normal_txcount(address, network='mainnet'):
    """获取账户交易数"""
    req_url = f"https://" \
              f"{urls[network]}" \
              f"/api?" \
              f"module=account&" \
              f"action=txlist&" \
              f"address={address}&" \
              f"startblock=0&" \
              f"endblock=99999999&" \
              f"sort=asc&" \
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
            return len(data['result'])
        else:
            return 0
    else:
        print("API请求失败：", 'response.status_code ', response.status_code)


def _fetch_create_date(address, network='mainnet'):
    """获取创建日期"""
    req_url1 = f"https://" \
               f"{urls[network]}" \
               f"/api?" \
               f"module=account&" \
               f"action=txlistinternal&" \
               f"address={address}&" \
               f"startblock=0&" \
               f"endblock=99999999&" \
               f"page=1&" \
               f"offset=1&" \
               f"sort=asc&" \
               f"apikey={random_key()}"
    req_url2 = f"https://" \
               f"{urls[network]}" \
               f"/api?" \
               f"module=account&" \
               f"action=txlist&" \
               f"address={address}&" \
               f"startblock=0&" \
               f"endblock=99999999&" \
               f"page=1&" \
               f"offset=1&" \
               f"sort=asc&" \
               f"apikey={random_key()}"
    for i in range(5):
        try:
            response = requests.get(req_url1)
        except Exception as e:
            print(f"请求失败{e}，进入重试逻辑")
        else:
            time.sleep(0.1)
            break
    if response.status_code == 200:
        data = response.json()
        if data['status'] == '1':
            if data['result'][0]['contractAddress'].lower() == address.lower():
                return _time_stamp_to_date(data['result'][0]['timeStamp'])
        else:
            print("API请求失败：", "message: ", data['message'], "result: ", data['result'])
            if len(data['result']) != 0:
                raise Exception('网络错误!')
    else:
        print("API请求失败：", 'response.status_code ', response.status_code)
        raise Exception('网络错误!')
    for i in range(5):
        try:
            response = requests.get(req_url2)
        except Exception as e:
            print(f"请求失败{e}，进入重试逻辑")
        else:
            time.sleep(0.1)
            break
    if response.status_code == 200:
        data = response.json()
        if data['status'] == '1':
            return _time_stamp_to_date(data['result'][0]['timeStamp'])
        else:
            print("API请求失败：", "message: ", data['message'], "result: ", data['result'])
            if len(data['result']) != 0:
                raise Exception('网络错误!')
    else:
        print("API请求失败：", 'response.status_code ', response.status_code)
        raise Exception('网络错误!')
