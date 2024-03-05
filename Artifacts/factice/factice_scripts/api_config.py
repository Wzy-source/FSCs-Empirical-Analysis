import random

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
