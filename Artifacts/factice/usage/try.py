import json
from tqdm import tqdm
from utils import find_main_contract_code_by_id, get_all_relations
MAX_CONSTRACT_ID=360000

def travel_all_constract(travel_list):
    NoneSourceCode=0
    for id in tqdm(travel_list):
        find_results=find_main_contract_code_by_id(id)
        if find_results is None or find_results[1] is None:
            NoneSourceCode+=1
            continue
        #print(find_results[0],'\n',find_results[1][:100])
    print("NoneSourceCodeNumber",NoneSourceCode)
            
if __name__ == '__main__':
    travel_list=range(MAX_CONSTRACT_ID) 
    #travel_all_constract(travel_list)
    print(get_all_relations())