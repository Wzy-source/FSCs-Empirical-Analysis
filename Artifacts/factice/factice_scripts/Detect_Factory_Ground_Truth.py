import json
import threading

import requests
from evmdasm import EvmBytecode
from mysql.api import DatabaseApi
from mysql.dao.fsc_validation import FSC_Validation


# 获取bytecode
def get_contract_bytecode(addr):
    alchemy_api_key = "JiPiyiAu0KZvZh5oRwi7bKFv7nmCwd8Q"
    # Alchemy API URL, replace YOUR_API_KEY with your actual API key from Alchemy
    ALCHEMY_API_URL = f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_api_key}"

    # Prepare the payload for the JSON-RPC request
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getCode",
        "params": [addr, "pending"],  # "latest" means get the code from the latest block
        "id": 1
    }

    # Send the POST request to Alchemy API
    headers = {"Content-Type": "application/json"}
    response = requests.post(ALCHEMY_API_URL, data=json.dumps(payload), headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        response_json = response.json()
        bytecode = response_json.get("result", None)
        if bytecode and bytecode != "0x":
            return bytecode
        else:
            print("No bytecode found for the given address.")
    else:
        print(f"Error: Unable to fetch contract bytecode. Status Code: {response.status_code}")
        print(response.text)


def is_factory_contract(evm_bytecode: str):
    evmcode = EvmBytecode(evm_bytecode)  # can be hexstr, 0xhexstr or bytes
    evminstructions = evmcode.disassemble()  # returns an EvmInstructions object (actually a list of new instruction objects)
    return any(instr.name in ["CREATE", "CREATE2"] for instr in evminstructions)


def filter_all_factory_contracts():
    db_api = DatabaseApi()
    network = "mainnet"
    all_contract_file_ids = db_api.select_all_contract_file_ids(chain=network)
    thread_num = 16
    part_size = len(all_contract_file_ids) // thread_num  # 向下取整，剩下的部分暂时忽略
    threads = []
    for i in range(thread_num):
        start_idx = i * part_size
        end_idx = start_idx + part_size
        thread = threading.Thread(target=filter_factory_contracts_one_thread, args=(i + 1, start_idx, end_idx, all_contract_file_ids))
        threads.append(thread)
        thread.start()
    end_thread = threading.Thread(target=filter_factory_contracts_one_thread,
                                  args=(thread_num + 1, thread_num * part_size, len(all_contract_file_ids), all_contract_file_ids))
    threads.append(end_thread)
    end_thread.start()
    # 等待所有线程执行结束
    for thread in threads:
        thread.join()


def filter_factory_contracts_one_thread(thread_id, start_idx, end_idx, all_contract_ids):
    db_api = DatabaseApi()
    traverse_num = 0
    for idx in range(start_idx, end_idx):
        traverse_num += 1
        cf_id = all_contract_ids[idx]
        contract_file = db_api.find_contract_file_by_id(cf_id)
        if len(contract_file.source_code) == 0:
            continue
        validation_re = db_api.select_fsc_validation_by_contract_file_id(cf_id)
        if validation_re.id != -1:
            continue
        name = contract_file.name
        address = contract_file.address
        network = contract_file.chain
        try:
            bytecode = get_contract_bytecode(address)
            print(f"get bytecode for {name}")
            is_factory = is_factory_contract(bytecode)
            db_api.save_fsc_validation_res(FSC_Validation(
                contract_file_id=cf_id,
                address=address,
                name=name,
                chain=network,
                is_factory_truth=is_factory
            ))
            print(f"线程{thread_id}成功保存{name}:{address},is_factory: {is_factory}")
            traverse_percentage = "{:.2f}%".format((traverse_num / (end_idx - start_idx)) * 100)
            print(f"thread{thread_id}修改进度为:{traverse_percentage}")
        except Exception as e:
            print(e)


if __name__ == '__main__':
    filter_all_factory_contracts()
