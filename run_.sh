cd chatbot_bert
out=$(pwd)
echo $out
source ./env/bin/activate
echo $(python3 --version)
# sudo pip install rasa
# sudo pip install pyvi==0.1.1 underthesea==6.5.0 underthesea_core==1.0.4 pandas==2.0.3 transformers
now=$(date +'%r %d/%m/%Y')
rasa train nlu --fixed-model-name "model_train_$now"