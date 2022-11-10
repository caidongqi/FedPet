# change stalness to False in pet/modeling.py
# change vote_k to True in pet/modeling.py
# remove prefix stale to filename in run_fed_aug.sh

infer_freq=10
datapoint=5
device=2

nohup python sweep_aug.py --dataset agnews --device ${device} --train_examples 64 --test_examples -1 --unlabeled_examples -1 --method fedpet --client_num_in_total 32 --all_client_num_in_total 1000 --alpha 1 --gamma 100 --pattern_ids 1 --data_point ${datapoint} --num_clients_infer 5 --infer_freq ${infer_freq} --model_name_or_path roberta-large &

nohup python sweep_aug.py --dataset mnli --device ${device} --train_examples 64 --test_examples -1 --unlabeled_examples -1 --method fedpet --client_num_in_total 32 --all_client_num_in_total 1000 --alpha 0 --gamma 100 --pattern_ids 0 --data_point ${datapoint} --num_clients_infer 5 --infer_freq ${infer_freq} --model_name_or_path roberta-large &

nohup python sweep_aug.py --dataset yahoo --device ${device} --train_examples 64 --test_examples -1 --unlabeled_examples -1 --method fedpet --client_num_in_total 32 --all_client_num_in_total 1000 --alpha 0 --gamma 100 --pattern_ids 5 --data_point ${datapoint} --num_clients_infer 5 --infer_freq ${infer_freq} --model_name_or_path roberta-large &

nohup python sweep_aug.py --dataset yelp-full --device ${device} --train_examples 64 --test_examples -1 --unlabeled_examples -1 --method fedpet --client_num_in_total 32 --all_client_num_in_total 1000 --alpha 0 --gamma 100 --pattern_ids 0 --data_point ${datapoint} --num_clients_infer 5 --infer_freq ${infer_freq} --model_name_or_path roberta-large &