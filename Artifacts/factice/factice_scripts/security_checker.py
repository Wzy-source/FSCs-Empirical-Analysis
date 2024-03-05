import os
from mysql.api import DatabaseApi, SenderInConstructor, AddressValidation, ImplementContractValidation
from utils import random_key
import subprocess
import time

python_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "env/bin/python")
export_directory = os.path.join(os.environ['HOME'], 'tempcode')
NO_SOURCE_CODE_TEXT1 = "Source code not available, try to fetch the bytecode only"
NO_SOURCE_CODE_TEXT2 = "If you are trying to analyze a contract from etherscan or similar make sure it has source code available."
CRASHED_TEXT = "ERROR:root:"
# Factory Address
FACTORY_FN_NOT_FOUND_TEXT = "err: factory function not found"
ADDR_NAME_NOT_FOUND_TEXT = "err: address name not found"
BY_NEW_TEXT = "factory create contract by new Contract"
BY_CREATE_TEXT = "factory create contract by create opcode"
BY_CREATE2_TEXT = "factory create contract by create2 opcode"
CHECK_ADDR_EQUAL_TEXT = "check if actual address is equal to target address"
CHECK_ADDR_0_TEXT = "check if actual address is 0"
CHECK_EXTCODE_TEXT = "check extcodesize or extcodehash of actual address"

# Clone Based Factory Detect0-
CHECK_IMP_ADDR_0_TEXT = "check_implement_address_equal_0"
CHECK_IMP_IS_CONTRACT_TEXT = "check_implement_is_contract"
CHECK_CALL_PROXY_TEXT = "check_call_proxy_contract"
CHECK_ADDRESS_IN_WHITELIST_TEXT = "check_address_in_whitelist"
INTERNAL_ADDRESS_TEXT = "is_internal_address"
EXTERNAL_ADDRESS_TEXT = "is_external_address"
IS_CLONE_BASED_FACTORY_TEXT = "is_clone_based_factory"
NO_CHECK_TEXT = "factory_no_check"
NETWORK_ERR_TEXT = "Connection reset by peer"


def check_created_contract_issues(created_addr, network):
    DETECTOR_REPORT_TEXT = "use msg.sender in created contract"
    db_client = DatabaseApi()
    temp_addr = ''
    if network != "mainnet":
        temp_addr = f"{network}:{created_addr}"
    command = f"{python_env_path} -m slither {temp_addr}" \
              f" --etherscan-export-directory {export_directory}" \
              f" --etherscan-apikey {random_key()}" \
              f" --detect created-security"
    print(command)
    start_ns = time.perf_counter_ns()
    result = subprocess.run(command, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    end_ns = time.perf_counter_ns()
    print(f"STDERR: {result.stderr}")
    if DETECTOR_REPORT_TEXT in result.stderr:  # 成功检测存在问题
        db_client.save_sender_in_constructor(SenderInConstructor(
            address=created_addr,
            chain=network,
            process_start=start_ns,
            process_end=end_ns,
            execute_time=end_ns - start_ns,
            crashed=False,
            has_source_code=True,
            has_issue=True
        ))
        print(f"detect!{created_addr, network}")
    elif (NO_SOURCE_CODE_TEXT1 in result.stderr) or (NO_SOURCE_CODE_TEXT2 in result.stderr):
        # 在NO_SOURCE_CODE情况下，Slither也会抛出错误，所以NO_SOURCE_CODE应放在Crashed之前判断
        db_client.save_sender_in_constructor(SenderInConstructor(
            address=created_addr,
            chain=network,
            process_start=start_ns,
            process_end=end_ns,
            execute_time=end_ns - start_ns,
            crashed=False,
            has_source_code=False,
            has_issue=False
        ))
        print(f"no source code!{created_addr, network}")
    elif "Connection reset by peer" in result.stderr:
        print("网络错误")
    elif CRASHED_TEXT in result.stderr:
        db_client.save_sender_in_constructor(SenderInConstructor(
            address=created_addr,
            chain=network,
            process_start=start_ns,
            process_end=end_ns,
            execute_time=end_ns - start_ns,
            crashed=True,
            has_source_code=True,
            has_issue=False
        ))
        print(f"crashed!{created_addr, network}")
    else:
        db_client.save_sender_in_constructor(SenderInConstructor(
            address=created_addr,
            chain=network,
            process_start=start_ns,
            process_end=end_ns,
            execute_time=end_ns - start_ns,
            crashed=False,
            has_source_code=True,
            has_issue=False
        ))
        print(f"正常执行{created_addr, network}")


def check_factory_contract_issues(factory_addr, network):
    temp_addr = ''
    if network != "mainnet":
        temp_addr = f"{network}:{factory_addr}"
    command = f"{python_env_path} -m slither {temp_addr}" \
              f" --etherscan-export-directory {export_directory}" \
              f" --etherscan-apikey {random_key()}" \
              f" --detect factory-security"
    print(command)
    db_client = DatabaseApi()
    start_ns = time.perf_counter_ns()
    result = subprocess.run(command, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    end_ns = time.perf_counter_ns()
    print(f"STDERR: {result.stderr}")
    if (NO_SOURCE_CODE_TEXT1 in result.stderr) or (NO_SOURCE_CODE_TEXT2 in result.stderr):
        db_client.save_address_validation(AddressValidation(
            address=factory_addr,
            chain=network,
            process_start=start_ns,
            process_end=end_ns,
            execute_time=end_ns - start_ns,
        ))
        print(f"no source code!{factory_addr, network}")
    elif "Connection reset by peer" in result.stderr:
        print("网络错误")
    elif CRASHED_TEXT in result.stderr:
        db_client.save_address_validation(AddressValidation(
            address=factory_addr,
            chain=network,
            process_start=start_ns,
            process_end=end_ns,
            execute_time=end_ns - start_ns,
            crashed=True
        ))
        print(f"crashed!{factory_addr, network}")
    else:
        factory_fn_not_found = FACTORY_FN_NOT_FOUND_TEXT in result.stderr
        addr_name_not_found = ADDR_NAME_NOT_FOUND_TEXT in result.stderr
        by_new = BY_NEW_TEXT in result.stderr
        by_create = BY_CREATE_TEXT in result.stderr
        by_create2 = BY_CREATE2_TEXT in result.stderr
        check_addr_equal = CHECK_ADDR_EQUAL_TEXT in result.stderr
        check_addr0 = CHECK_ADDR_0_TEXT in result.stderr
        check_extcode = CHECK_EXTCODE_TEXT in result.stderr
        db_client.save_address_validation(AddressValidation(
            address=factory_addr,
            chain=network,
            process_start=start_ns,
            process_end=end_ns,
            execute_time=end_ns - start_ns,
            crashed=False,
            has_source_code=True,
            factory_fn_not_found=factory_fn_not_found,
            addr_name_not_found=addr_name_not_found,
            by_new=by_new,
            by_create=by_create,
            by_create2=by_create2,
            check_addr_equal=check_addr_equal,
            check_extcode=check_extcode,
            check_addr0=check_addr0
        ))
        print(f"err:factory_fn_not_found: {factory_fn_not_found}\n"
              f"err:addr_name_not_found: {addr_name_not_found}\n"
              f"by_new :{by_new}\n"
              f"by_create: {by_create}\n"
              f"by_create2: {by_create2}\n"
              f"check_addr_equal: {check_addr_equal}\n"
              f"check_addr0: {check_addr0}\n"
              f"check_extcode: {check_extcode}")
        print(f"analysed!{factory_addr, network}")


def check_clone_based_factory_issues(factory_addr, network):
    temp_addr = ''
    if network != "mainnet":
        temp_addr = f"{network}:{factory_addr}"
    command = f"{python_env_path} -m slither {temp_addr}" \
              f" --etherscan-export-directory {export_directory}" \
              f" --etherscan-apikey {random_key()}" \
              f" --detect clone-based-factory-security"
    print(command)
    db_client = DatabaseApi()
    start_ns = time.perf_counter_ns()
    result = subprocess.run(command, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    end_ns = time.perf_counter_ns()
    print(f"STDERR: {result.stderr}")
    if NETWORK_ERR_TEXT in result.stderr:
        print('网络错误')
    elif CRASHED_TEXT in result.stderr:
        db_client.save_implement_contract_validation(ImplementContractValidation(
            address=factory_addr,
            chain=network,
            process_start=start_ns,
            process_end=end_ns,
            execute_time=end_ns - start_ns,
            crashed=True,
            has_source_code=True,
        ))
    else:
        check_imp_addr0 = CHECK_IMP_ADDR_0_TEXT in result.stderr
        check_imp_is_contract = CHECK_IMP_IS_CONTRACT_TEXT in result.stderr
        check_call_proxy = CHECK_CALL_PROXY_TEXT in result.stderr
        check_addr_in_whitelist = CHECK_ADDRESS_IN_WHITELIST_TEXT in result.stderr
        internal_addr = INTERNAL_ADDRESS_TEXT in result.stderr
        external_addr = EXTERNAL_ADDRESS_TEXT in result.stderr
        is_clone_based_factory = IS_CLONE_BASED_FACTORY_TEXT in result.stderr
        no_check = NO_CHECK_TEXT in result.stderr
        db_client.save_implement_contract_validation(ImplementContractValidation(
            address=factory_addr,
            chain=network,
            process_start=start_ns,
            process_end=end_ns,
            execute_time=end_ns - start_ns,
            crashed=False,
            has_source_code=True,
            is_clone_based_factory=is_clone_based_factory,
            not_check=no_check,
            check_addr0=check_imp_addr0,
            check_is_contract=check_imp_is_contract,
            in_whitelist=check_addr_in_whitelist,
            check_fn_call=check_call_proxy,
            external_address=external_addr,
            internal_address=internal_addr
        ))


def check_created_issues_by_slither(created_addr):
    """
    使用原生slither检查所有有源码的created合约的安全性问题
    """
    command = f"{python_env_path} -m slither {created_addr}" \
              f" --etherscan-export-directory {export_directory}" \
              f" --etherscan-apikey {random_key()}"
    try:
        subprocess.run(command, shell=True, check=True)
    except Exception as e:
        print(f'运行check_created_issues_by_slither时出现错误，{e}')
    else:
        print(f'成功处理address{created_addr}')


def delete_temp_project():
    project_path = os.path.join(os.environ['HOME'], 'tempcode/*')
    remove_command = f"rm -r {project_path}"
    try:
        subprocess.run(remove_command, shell=True, check=True)
        print(f'临时项目 {project_path} 已成功删除')
    except Exception as e:
        print(f'删除文件时发生错误：{e}')


def created_detect():
    db_client = DatabaseApi()
    # 先检测created相关问题, network为mainnet
    created_ids = db_client.find_id_by_chain_and_contract_type('sepolia', 'created')  # unique source code
    traverse_count = 0
    for created_id in created_ids:
        created_contract = db_client.find_contract_file_by_id(created_id)
        created_addr = created_contract.address
        network = created_contract.chain
        sender_in_const_id = db_client.find_sender_in_constructor_by_chain_and_address(network, created_addr).id
        if sender_in_const_id == -1:
            check_created_contract_issues(created_addr, network)
        traverse_count += 1
        traverse_percentage = "{:.2f}%".format((traverse_count / len(created_ids)) * 100)
        print(f"created detect遍历进度为：{traverse_percentage}")
    print("Created Detect Complete!!!")


def factory_detect():
    db_client = DatabaseApi()
    # TODO 先检查mainnet的
    factory_ids = db_client.find_id_by_chain_and_contract_type('sepolia', 'factory')
    traverse_count = 0
    for factory_id in factory_ids:
        fc = db_client.find_contract_file_by_id(factory_id)
        add_valid_id = db_client.find_address_validation_by_chain_and_address(fc.chain, fc.address).id
        if add_valid_id == -1:
            check_factory_contract_issues(fc.address, fc.chain)
        traverse_count += 1
        traverse_percentage = "{:.2f}%".format((traverse_count / len(factory_ids)) * 100)
        print(f"factory detect遍历进度为：{traverse_percentage}")
    print("Factory Detect Complete!!!")


def clone_based_factory_detect():
    db_client = DatabaseApi()
    # TODO 先检查mainnet的
    factory_ids = db_client.find_id_by_chain_and_contract_type('sepolia', 'factory')
    traverse_count = 0
    for factory_id in factory_ids:
        fc = db_client.find_contract_file_by_id(factory_id)
        clone_based_id = db_client.find_implement_contract_validation_by_chain_and_address(fc.chain, fc.address).id
        if clone_based_id == -1:
            check_clone_based_factory_issues(fc.address, fc.chain)
        traverse_count += 1
        traverse_percentage = "{:.2f}%".format((traverse_count / len(factory_ids)) * 100)
        print(f"clone based factory detect遍历进度为：{traverse_percentage}")
    print("Clone Based Factory Detect Complete")


if __name__ == '__main__':
    clone_based_factory_detect()
    delete_temp_project()
