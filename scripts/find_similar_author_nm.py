from os.path import join

from json import dump

import pandas as pd

from thefuzz import fuzz

CODEBASE_NM = 'sklearn'

def compute_author_nm_mapping(sr, threshold=80):
    mapping = {}  
    already_processed = set()
    
    for _, author_nm in sr.iteritems():
        
        if author_nm in already_processed:
            continue
        
        already_processed.add(author_nm)
        mapping[author_nm] = []

        for _, other_author_nm in sr.iteritems():
            
            if other_author_nm == author_nm or other_author_nm in already_processed:
                continue
            
            similarity = fuzz.ratio(author_nm, other_author_nm)
            if similarity > threshold:
                mapping[author_nm].append(other_author_nm)
                already_processed.add(other_author_nm)

        if len(mapping[author_nm]) == 0:
            del mapping[author_nm]
    
    return mapping


f_path = join('.', 'data', f'{CODEBASE_NM}_raw_commit.csv')
sr_author_nm = pd.read_csv(f_path)['author_nm'].drop_duplicates()
author_nm_mapping = compute_author_nm_mapping(sr_author_nm, threshold=80)

f_path = join('.', 'data', f"{CODEBASE_NM}_author_nm_merging.json")
with open(f_path, 'w') as f:
    dump(author_nm_mapping, f, indent=4)