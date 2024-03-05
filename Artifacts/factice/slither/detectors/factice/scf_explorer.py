import os
from typing import List, Tuple
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output
import requests, json
# from py_scripts.preprocess_contracts import save_temp_project
from slither.detectors.factice.utils import save_source_code, get_home_folder_path

remappings_test_addr = "0x00000000000006c7676171937C444f6BDe3D6282"


class SCFExplorer(AbstractDetector):
    ARGUMENT = 'scf-explorer'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.MEDIUM
    HELP = "detect factory-related smart contracts"
    WIKI = "https://github.com/crytic/slither/wiki/factory-detect#non-standard-proxy"
    WIKI_TITLE = "Factory Explorer"
    WIKI_DESCRIPTION = """
    Detect factory-related smart contracts
    """
    WIKI_RECOMMENDATION = """
    None
    """

    def _detect(self) -> List[Output]:
        results = []
        # 从self中获取factory_contract_addr
        # factory_contract_name = self
        address = remappings_test_addr
        contract_name, source_code = fetch_verified_contract_name_and_source_code(address)
        # 该合约地址存在可能没有verified_source_code的情况
        if contract_name and source_code:
            # # 将合约保存为"name_address"形式
            # filename = f"{address}_{contract_name}.sol"
            # destination_folder_path = get_home_folder_path("factory-related-contracts")
            # # 保存文件至本地
            # save_source_code(filename, source_code, destination_folder_path)
            project_path = os.path.join("/Users/mac/Desktop", 'temp_codes')
            target_file_name = f"mainnet_{address}_{contract_name}.sol"

            # save_temp_project(project_path, target_file_name, source_code)
        return results


def find_matched_remapping_rule(path: str, remappings: list) -> str:
    matched_rule = ""
    longest_prefix = ""
    for rule in remappings:
        # Import remappings have the form of context:prefix=target
        cp_t = rule.split("=")
        prefix, target = cp_t[0], cp_t[1]
        if path.startswith(prefix) and len(prefix) >= len(longest_prefix):
            longest_prefix = prefix
            matched_rule = rule
    return matched_rule


"""
Etherscan相关API
"""

API_KEY = "IITPA3E4JGAUSJ8ZFT24CE3E3NV7RFR4WN"


def fetch_verified_contract_name_and_source_code(address) -> Tuple[str, str]:
    """
    根据智能合约地址获取验证过的合约源代码
    """
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


def extract_address_in_filename(filename) -> str:
    parts = filename.split("_")
    if len(parts) > 0:
        return parts[0]
    return ""
