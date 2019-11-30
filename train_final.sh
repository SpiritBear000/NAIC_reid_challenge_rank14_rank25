#!/usr/bin/bash

# config_file
config_file=configs/${1}.yml
# output_dir
output_dir=/mnt/anxiang/models/reid_exp/${1}
# train_root
train_root=/home/xiangan/code_and_data/train_split/all_final
# test_root
test_root=/home/xiangan/data_reid/testB
# model_pretrain_path
model_pretrain_path=${output_dir}/se_resnet50_model_120.pth

echo "config files is ${config_file}"
echo "save path is ${output_dir}"

python tools/train.py \
    --config_file=${config_file} \
    MODEL.DEVICE_ID "('0,1')" \
    DATASETS.ROOT_DIR "('${train_root}')" \
    OUTPUT_DIR "('${output_dir}')"

python extract_final.py \
    --config_file=${config_file} \
    MODEL.DEVICE_ID "('0')" \
    DATASETS.ROOT_DIR ${test_root} \
    MODEL.PRETRAIN_CHOICE "('self')" \
    MODEL.PRETRAIN_PATH "('${model_pretrain_path}')" \
    OUTPUT_DIR "('./features_testB/${1}')"

python get_submission.py --name "${1}"