from factice_scripts.utils import _fetch_create_txhash, _fetch_internal_txcount, _fetch_create_txs_by_txhash
from mysql.api import DatabaseApi, ContractFile
import requests


def fetch_verified_contract_name_and_source_code(address):
    """
    根据智能合约地址获取验证过的合约源代码
    """
    API_KEY = "IITPA3E4JGAUSJ8ZFT24CE3E3NV7RFR4WN"
    req_url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={address}&apikey={API_KEY}"
    response = requests.get(req_url)
    contract_name, source_code = "", ""
    if response.status_code == 200:
        data = response.json()
        if data['status'] == '1':
            contract_info = data['result'][0]
            # 如果是未验证的合约，返回的source_code和contract_name都为""
            source_code = contract_info['SourceCode']
            contract_name = contract_info['ContractName']
            print(contract_name, source_code)
        else:
            print("API请求失败：", data['message'], data['result'])
    else:
        print("API请求失败：", response.status_code)
    return contract_name, source_code


if __name__ == '__main__':
    address = '0xf0277caffea72734853b834afc9892461ea18474'
    # create_txhash = _fetch_create_txhash(address)
    print(_fetch_internal_txcount(address, 'goerli'))
    create_txhash = "0x5f9752135719df8925d69bace9c1d466dead31ea932b9d62e593a1d46c8cef14"
    create_txs = _fetch_create_txs_by_txhash(create_txhash)
    if create_txs and len(create_txs) > 0:
        for create_tx in create_txs:
            fac_addr = create_tx['from']
            created_addr = create_tx['contractAddress']
            print(f"from_addr:{fac_addr},contractAddr:{created_addr}")
