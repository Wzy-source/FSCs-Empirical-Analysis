import requests
from lxml import html
import re
import time
import random

from mysql.api import DatabaseApi, ContractFile

test_url = "https://etherscan.io/txs?a=0x0000000000ffe8b47b3e2130213b802212439497"
urls = {
    "mainnet": "etherscan.io",
    "goerli": "goerli.etherscan.io",
    "sepolia": "sepolia.etherscan.io",
}


def scrape_contract_tx_num(address, network):
    # 发送HTTP请求获取网页内容
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    url = "https://" + urls[network] + "/txs?a=" + address
    response = requests.get(url, headers=headers)

    # 检查请求是否成功
    if response.status_code == 200:
        tree = html.fromstring(response.content)

    # 使用XPath表达式选择元素
    xpath = '/html/body/main/section[3]/div[1]/div[1]/div/div[1]/span'
    selected_element = tree.xpath(xpath)[0]
    # 打印选定元素的内容
    select_str: str = selected_element.text_content()
    total_transactions = int(select_str.replace(",", "").replace("A total of ", "").replace("transactions found", ""))
    print("总交易数:", total_transactions)
    return total_transactions


def modify_contracts_tx_num():
    db_client = DatabaseApi()
    contract_ids = db_client.find_max_tx_contracts()
    for id in contract_ids:
        cf = db_client.find_contract_file_by_id(id)
        tx_num = scrape_contract_tx_num(cf.address, cf.chain)
        print(f"network: {cf.chain}, address: {cf.address}, tx_num: {tx_num}")
        cf.txcount = tx_num
        db_client.save_contract_file(cf)
        # time.sleep(random.uniform(1, 3))


if __name__ == '__main__':
    modify_contracts_tx_num()
