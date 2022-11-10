import os
import json
from tqdm import tqdm
from collections import defaultdict
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import torch

import logging
process_id = os.getpid()
logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO,
                        format=str(
                            process_id) + ' - %(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S')

# nohup python sweep_aug.py --dataset agnews --device 0 --train_examples 0 --test_examples -1 --unlabeled_examples -1 --method fedpet --client_num_in_total 32 --all_client_num_in_total 1000 --seed 6 --pattern_ids 1 --alpha 1 --data_point 5 --num_clients_infer 5 --infer_freq 1 &

def calculate_sentence_transformer_embedding(text_to_encode):
    num = len(text_to_encode)
    emb_model = SentenceTransformer('sentence-transformers/paraphrase-mpnet-base-v2')
    embeddings = []
    bar = tqdm(range(0,num,20),desc='calculate embeddings')
    for i in range(0,num,20):
        embeddings += emb_model.encode(text_to_encode[i:i+20]).tolist()
        bar.update(1)
    embeddings = torch.tensor(embeddings)
    mean_embeddings = torch.mean(embeddings, 0, True)
    embeddings = embeddings - mean_embeddings
    return embeddings

def text_to_encode(train_examples, dataset):
    if dataset == "agnews":
        return ["{}(){}".format(raw_item.to_dict()["text_a"], raw_item.to_dict()["text_b"]) for raw_item in train_examples]
    elif dataset == "mnli":
        return ["{}.\nquestion: {}".format(raw_item.to_dict()["text_a"], raw_item.to_dict()["text_b"]) for raw_item in train_examples]
    elif dataset == "yahoo":
        return ["question: {}.\nanswer: {}".format(raw_item.to_dict()["text_a"], raw_item.to_dict()["text_b"]) for raw_item in train_examples]
    elif dataset == "yelp":
        return ["{}".format(raw_item.to_dict()["text_a"]) for raw_item in train_examples]
    else:
        raise ValueError("dataset not supported")

def select_by_voting(train_examples, select_num, output_dir, dataset, k = 150):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    vote_file=os.path.join(output_dir,'votek_cache.json')

    if vote_file is not None and os.path.isfile(vote_file): # will load from json file if exists.
        logging.info(f'load from {vote_file}')
        embeddings=[]
    else:
        all_train_text_to_encode = text_to_encode(list(train_examples), dataset)
        embeddings = calculate_sentence_transformer_embedding(text_to_encode=all_train_text_to_encode)

    selected_indices = fast_votek(embeddings=embeddings,
                                  select_num=select_num,
                                  k=k,
                                  vote_file=os.path.join(output_dir,'votek_cache.json'))
    selected_examples = []
    for idx in selected_indices:
        selected_examples.append(train_examples[idx])
    return selected_examples

def fast_votek(embeddings,select_num,k,vote_file=None):
    n = len(embeddings)
    if vote_file is not None and os.path.isfile(vote_file):
        with open(vote_file) as f:
            vote_stat = json.load(f)
    else:
        bar = tqdm(range(n),desc=f'voting')
        vote_stat = defaultdict(list)
        for i in range(n):
            cur_emb = embeddings[i].reshape(1, -1)
            cur_scores = np.sum(cosine_similarity(embeddings, cur_emb), axis=1)
            sorted_indices = np.argsort(cur_scores).tolist()[-k-1:-1]
            for idx in sorted_indices:
                if idx!=i:
                    vote_stat[idx].append(i)
            bar.update(1)
        if vote_file is not None:
            with open(vote_file,'w') as f:
                json.dump(vote_stat,f)
    votes = sorted(vote_stat.items(),key=lambda x:len(x[1]),reverse=True)
    selected_indices = []
    selected_times = defaultdict(int)
    while len(selected_indices)<select_num:
        cur_scores = defaultdict(int)
        for idx,candidates in votes:
            if idx in selected_indices:
                cur_scores[idx] = -100
                continue
            for one_support in candidates:
                if not one_support in selected_indices:
                    cur_scores[idx] += 10 ** (-selected_times[one_support]) # if one_support not been selected, add 1, or add **.
        cur_selected_idx = max(cur_scores.items(),key=lambda x:x[1])[0] # discourage idx that has been selected to encourage diversity.
        selected_indices.append(int(cur_selected_idx))
        for idx_support in vote_stat[cur_selected_idx]:
            selected_times[idx_support] += 1
    return selected_indices