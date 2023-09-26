# -*- coding: utf-8 -*-
"""As4_Deep_Learning_Casari_final.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1AB_ejx3oYWsxkjVYxfACG3a5moHiy4ie
"""

import os
import time
from tqdm import tqdm
import torch
import torch.nn as nn
#torch.cuda.empty_cache()

from torch.utils.data import Dataset


class Vocabulary:

    def __init__(self, pad_token="<pad>", unk_token='<unk>', eos_token='<eos>',
                 sos_token='<sos>'):
        self.id_to_string = {}
        self.string_to_id = {}
        
        # add the default pad token
        self.id_to_string[0] = pad_token
        self.string_to_id[pad_token] = 0
        
        # add the default unknown token
        self.id_to_string[1] = unk_token
        self.string_to_id[unk_token] = 1
        
        # add the default unknown token
        self.id_to_string[2] = eos_token
        self.string_to_id[eos_token] = 2   

        # add the default unknown token
        self.id_to_string[3] = sos_token
        self.string_to_id[sos_token] = 3

        # shortcut access
        self.pad_id = 0
        self.unk_id = 1
        self.eos_id = 2
        self.sos_id = 3

    def __len__(self):
        return len(self.id_to_string)

    def add_new_word(self, string):
        self.string_to_id[string] = len(self.string_to_id)
        self.id_to_string[len(self.id_to_string)] = string

    # Given a string, return ID
    # if extend_vocab is True, add the new word
    def get_idx(self, string, extend_vocab=False):
        if string in self.string_to_id:
            return self.string_to_id[string]
        elif extend_vocab:  # add the new word
            self.add_new_word(string)
            return self.string_to_id[string]
        else:
            return self.unk_id


# Read the raw txt files and generate parallel text dataset:
# self.data[idx][0] is the tensor of source sequence
# self.data[idx][1] is the tensor of target sequence
# See examples in the cell below.
class ParallelTextDataset(Dataset):

    def __init__(self, src_file_path, tgt_file_path, src_vocab=None,
                 tgt_vocab=None, extend_vocab=False, device='cuda'):
        (self.data, self.src_vocab, self.tgt_vocab, self.src_max_seq_length,
         self.tgt_max_seq_length) = self.parallel_text_to_data(
            src_file_path, tgt_file_path, src_vocab, tgt_vocab, extend_vocab,
            device)

    def __getitem__(self, idx):
        return self.data[idx]

    def __len__(self):
        return len(self.data)

    def parallel_text_to_data(self, src_file, tgt_file, src_vocab=None,
                              tgt_vocab=None, extend_vocab=False,
                              device='cuda'):
        # Convert paired src/tgt texts into torch.tensor data.
        # All sequences are padded to the length of the longest sequence
        # of the respective file.

        assert os.path.exists(src_file)
        assert os.path.exists(tgt_file)

        if src_vocab is None:
            src_vocab = Vocabulary()

        if tgt_vocab is None:
            tgt_vocab = Vocabulary()
        
        data_list = []
        # Check the max length, if needed construct vocab file.
        src_max = 0
        with open(src_file, 'r') as text:
            for line in text:
                tokens = list(line)[:-1]  # remove line break
                length = len(tokens)
                if src_max < length:
                    src_max = length

        tgt_max = 0
        with open(tgt_file, 'r') as text:
            for line in text:
                tokens = list(line)[:-1]
                length = len(tokens)
                if tgt_max < length:
                    tgt_max = length
        tgt_max += 2  # add for begin/end tokens
                    
        src_pad_idx = src_vocab.pad_id
        tgt_pad_idx = tgt_vocab.pad_id

        tgt_eos_idx = tgt_vocab.eos_id
        tgt_sos_idx = tgt_vocab.sos_id

        # Construct data
        src_list = []
        print(f"Loading source file from: {src_file}")
        with open(src_file, 'r') as text:
            for line in tqdm(text):
                seq = []
                tokens = list(line)[:-1]
                for token in tokens:
                    seq.append(src_vocab.get_idx(
                        token, extend_vocab=extend_vocab))
                var_len = len(seq)
                var_seq = torch.tensor(seq, device=device, dtype=torch.int64)
                # padding
                new_seq = var_seq.data.new(src_max).fill_(src_pad_idx)
                new_seq[:var_len] = var_seq
                src_list.append(new_seq)

        tgt_list = []
        print(f"Loading target file from: {tgt_file}")
        with open(tgt_file, 'r') as text:
            for line in tqdm(text):
                seq = []
                tokens = list(line)[:-1]
                # append a start token
                seq.append(tgt_sos_idx)
                for token in tokens:
                    seq.append(tgt_vocab.get_idx(
                        token, extend_vocab=extend_vocab))
                # append an end token
                seq.append(tgt_eos_idx)

                var_len = len(seq)
                var_seq = torch.tensor(seq, device=device, dtype=torch.int64)

                # padding
                new_seq = var_seq.data.new(tgt_max).fill_(tgt_pad_idx)
                new_seq[:var_len] = var_seq
                tgt_list.append(new_seq)

        # src_file and tgt_file are assumed to be aligned.
        assert len(src_list) == len(tgt_list)
        for i in range(len(src_list)):
            data_list.append((src_list[i], tgt_list[i]))

        print("Done.")
            
        return data_list, src_vocab, tgt_vocab, src_max, tgt_max

# !mkdir numbers__place_value

# `DATASET_DIR` should be modified to the directory where you downloaded
# the dataset. On Colab, use any method you like to access the data
# e.g. upload directly or access from Drive, ...

DATASET_DIR = "/content/drive/MyDrive"

TRAIN_FILE_NAME = "train"
VALID_FILE_NAME = "interpolate"

INPUTS_FILE_ENDING = ".x"
TARGETS_FILE_ENDING = ".y"

TASK = "numbers__place_value" # done
#TASK = "comparison__sort" # partially done
# TASK = "algebra__linear_1d" # not done

# Adapt the paths!

src_file_path = f"{DATASET_DIR}/{TASK}/{TRAIN_FILE_NAME}{INPUTS_FILE_ENDING}"
tgt_file_path = f"{DATASET_DIR}/{TASK}/{TRAIN_FILE_NAME}{TARGETS_FILE_ENDING}"
print(src_file_path)
train_set = ParallelTextDataset(src_file_path, tgt_file_path, extend_vocab=True)

# get the vocab
src_vocab = train_set.src_vocab
tgt_vocab = train_set.tgt_vocab

src_file_path = f"{DATASET_DIR}/{TASK}/{VALID_FILE_NAME}{INPUTS_FILE_ENDING}"
tgt_file_path = f"{DATASET_DIR}/{TASK}/{VALID_FILE_NAME}{TARGETS_FILE_ENDING}"

valid_set = ParallelTextDataset(
    src_file_path, tgt_file_path, src_vocab=src_vocab, tgt_vocab=tgt_vocab,
    extend_vocab=False)

from google.colab import drive
drive.mount('/content/drive')

from torch.utils.data import DataLoader

batch_size = 64
print(len(train_set))
train_data_loader = DataLoader(
    dataset=train_set, batch_size=batch_size, shuffle=True)
print(len(valid_set))
valid_data_loader = DataLoader(
    dataset=valid_set, batch_size=batch_size, shuffle=False)
del valid_set
del train_set

src_vocab.id_to_string

tgt_vocab.id_to_string

# Example batch
'''
batch = next(iter(train_data_loader))
print("shape of one batch ", len(batch))
print("dataloader has ", len(train_data_loader), " batches")
source = batch[0]  # source sequence
print(source.shape)
target = batch[1]  # target sequence

print(target.shape)
# verifying last batch
iterator=iter(train_data_loader)
last_batch = next(iterator)
for last_batch in iterator:
    continue
print("last batch has shape (training): ", last_batch[0].shape)
'''

'''
iterator=iter(valid_data_loader)
last_batch_val = next(iterator)
for last_batch_val in iterator:
    continue
print("last batch[0] has shape (validation): ", last_batch_val[0].shape)
print("last batch[1] has shape (validation): ", last_batch_val[1].shape)
batch = next(iter(valid_data_loader))
print("shape of one batch ", len(batch))
print("dataloader has ", len(valid_data_loader), " batches")
source = batch[0]  # source sequence
print(source.shape)
target = batch[1]  # target sequence

print(target.shape)
'''

# example source/target pair
example_source_sequence = []

for i in source[0]:
    example_source_sequence.append(src_vocab.id_to_string[i.item()])

print(example_source_sequence)
print("lenght of example source: ", len(example_source_sequence))

print(''.join(example_source_sequence))

example_target_sequence = []

for i in target[0]:
    example_target_sequence.append(tgt_vocab.id_to_string[i.item()])

print(example_target_sequence)
print("lenght of example source: ", len(example_target_sequence))

'''
batch=next(iter(train_data_loader))
count_char=0
array_lenght=[]
import numpy as np

for batch in iter(train_data_loader):
    source=batch[0].cuda()
    #target=batch[1]
    for question in source:
        count=0
        for id in question.cuda():
          count+=1
          if(id==0):
            array_lenght.append(count-1)
            break

            #char=src_vocab.id_to_string[id.item()]
            #print(char)
print("average of len of question for training set: ", np.mean(array_lenght))
#print(len(last_batch[0]))
print("number of characters of training: ", (len(last_batch[0])+(len(train_data_loader)*(batch_size-1))*50))
print("number of characters of training: ", (len(last_batch_val[0])+(len(valid_data_loader)*(batch_size-1))*48))
'''

'''
average_questions=np.mean(array_lenght)
std_train=np.std(array_lenght)
print(average_questions)
print(std_train)
# store variable
file = open("./var.txt", "w")

file.write("mean = " + str(average_questions) + "\n")
file.write("std = " + str(std_train) + "\n")
file.close()
'''

########
# Taken from:
# https://pytorch.org/tutorials/beginner/transformer_tutorial.html
# or also here:
# https://github.com/pytorch/examples/blob/master/word_language_model/model.py
import math
class PositionalEncoding(nn.Module):

    def __init__(self, d_model, dropout=0.0, max_len=5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)
        self.max_len = max_len

        pe = torch.zeros(max_len, d_model)
        #print("pe: ", pe.shape)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        #print(position.shape)
        #print(position)
        div_term = torch.exp(torch.arange(0, d_model, 2).float()
                             * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)  # shape (max_len, 1, dim)
        self.register_buffer('pe', pe)  # Will not be trained.

    def forward(self, x):
        """Inputs of forward function
        Args:
            x: the sequence fed to the positional encoder model (required).
        Shape:
            x: [sequence length, batch size, embed dim]
            output: [sequence length, batch size, embed dim]
        """
        assert x.size(0) < self.max_len, (
            f"Too long sequence length: increase `max_len` of pos encoding")
        # shape of x (len, B, dim)
        x = x + self.pe[:x.size(0), :]
        return self.dropout(x)

#batch=next(iter(valid_data_loader))
#for i in batch[0]:
#  print(i)

'''
batch=next(iter(valid_data_loader))
count_char=0
array_lenght=[]
import numpy as np
import time
start=time.time()
for batch in iter(valid_data_loader):
    source=batch[0]
    #target=batch[1]
    for question in source:
        count=0
        for id in question:
          count+=1
          if(id==0):
            array_lenght.append(count-1)
            break

            #char=src_vocab.id_to_string[id.item()]
            #print(char)
print("time of execution: ", time.time()-start)
print("average of len of questions for validation set: ", np.mean(array_lenght))
print("std of len of questions for validation set: ", np.std(array_lenght))
#print(len(last_batch[0]))
print("number of characters of validation: ", (len(last_batch[0])+(len(train_data_loader)*(batch_size-1))*50))
print("number of characters of validation: ", (len(last_batch_val[0])+(len(valid_data_loader)*(batch_size-1))*48))

'''
DEVICE='cuda:0'

class Embedder(nn.Module):
    def __init__(self, vocab_size, d_model):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, d_model, padding_idx=0)
    def forward(self, x):
        return self.embed(x)

class MyTransformer(nn.Module):

  def __init__(self, src_vocab, trg_vocab, d_model, num_enc_layers, num_dec_layers, nhead,hidden_size, dim_forwards):
    super(MyTransformer, self).__init__()
    
    self.d_model=d_model
    self.memory=None
    self.emb_layer_src=Embedder(src_vocab, d_model).cuda()
    self.emb_layer_tgt=Embedder(trg_vocab, d_model).cuda()
    self.memory_padding_mask=None
    self.positional_encoding_src=PositionalEncoding(d_model).cuda()
    self.positional_encoding_tgt=PositionalEncoding(d_model).cuda()

    self.transf= nn.Transformer(d_model, nhead,  num_enc_layers,num_dec_layers, dim_forwards, batch_first=True).cuda()
    self.linear = nn.Linear(hidden_size, trg_vocab).cuda()
    #self.out=nn.Softmax(len(trg_vocab))
    
  def forward(self, src, trg):
        
      src_emb = (self.emb_layer_src(src)).cuda()
      tgt_emb = (self.emb_layer_tgt(trg)).cuda()
      trg_mask= self.create_mask(trg).cuda()
      src_padding_mask= (src==src_vocab.string_to_id['<pad>'])
      self.memory_padding_mask= src_padding_mask.cuda()
      src_emb = self.positional_encoding_src(src_emb.transpose(0,1)).cuda()
      src_emb=src_emb.transpose(0,1)
      tgt_emb = self.positional_encoding_tgt(tgt_emb.transpose(0,1)).cuda()
      tgt_emb=tgt_emb.transpose(0,1)

      self.memory = self.transf.encoder(src_emb, mask=None, src_key_padding_mask=src_padding_mask).cuda()
      #print(f"memory shape {memory.shape}")
      
      outs = self.transf.decoder(tgt_emb, self.memory, tgt_mask=trg_mask, memory_mask=None,
                              tgt_key_padding_mask=None,
                              memory_key_padding_mask=src_padding_mask)
    
      outs = self.linear(outs)
      
      return outs

  def compute_accuracy(self, num_correct, num_sentences):
      return (float(num_correct)/num_sentences)*100.0
    
  def create_mask(self,tgt):
      #src_seq_len = src.shape[0]
      tgt_seq_len = tgt.size(1)
      tgt_mask = self.transf.generate_square_subsequent_mask(tgt_seq_len)
      #print(f"target mask shape: {tgt_mask.shape}")
      #src_mask = torch.zeros((src_seq_len, src_seq_len),device=DEVICE).type(torch.bool)
      #src_mask=self.transf.generate_square_subsequent_mask(src_seq_len)
      #src_padding_mask = (src == 0)
      #tgt_padding_mask = (tgt == 0)
      
      return tgt_mask.cuda()
  import time

  def greedy(self, src,  max_len=3, show_example=False):
    
    outs='<sos>'
    
    #char_out=outs
    outs=tgt_vocab.string_to_id[outs]
    src_emb = (self.emb_layer_src(src)).cuda() 
    src_padding_mask= (src==src_vocab.string_to_id['<pad>'])
    self.memory_padding_mask= src_padding_mask.cuda()
    src_emb = self.positional_encoding_src(src_emb.transpose(0,1)).cuda()
    src_emb=src_emb.transpose(0,1)
    self.memory = self.transf.encoder(src_emb, mask=None, src_key_padding_mask=src_padding_mask).cuda()
    outs=torch.full((self.memory.size(0),1), outs).cuda()
    prev_input=outs
    trg_mask= self.transf.generate_square_subsequent_mask(outs.size(1)).cuda()
    #print(f"tgt mask: {trg_mask}")
    #outs=torch.tensor([outs]).cuda()
    #outs=torch.full((64,2), '<sos>')
    tgt_emb = (self.emb_layer_tgt(outs)).cuda()
    tgt_emb = self.positional_encoding_tgt(tgt_emb).cuda()
    #print(tgt_emb)
    #print(f"shape of memory: {self.memory.shape} and shape of tgt_emb: {tgt_emb.shape}")
    length=1
    #flag_correct=False
    correct_answers=0
    c=0
    while(1):
      print(max_len)
      if(length>max_len):
        print("\n exiting in greddy because it reached the max len")
        break
      output= self.transf.decoder(tgt_emb, self.memory, tgt_mask=trg_mask, memory_mask=None,
                              tgt_key_padding_mask=None,
                              memory_key_padding_mask=self.memory_padding_mask).cuda()
      outs= self.linear(output).cuda()
      outputs=outs
      #char_out= tgt_vocab.id_to_string[(torch.argmax(outs, dim=2)[0][-1].item())]
      #print(f"\n char predicted : {char_out}", end=' , ')
      outs=torch.softmax(outs, dim=2)
      outs=torch.argmax(outs, dim=2)
      count_eos=0
      
      for seq in outs:
        
        char=seq[-1:]
        if(char==tgt_vocab.string_to_id['<eos>']):
          count_eos+=1
      if(count_eos==outs.size(0)):
        print(" \n exiting in greddy because all seq reached <eos>")
        break
          

      #true_answers= (outs == tgt_out[:,:outs.size(1)])
     

      if(length==1):
        outs=torch.cat([prev_input, outs], dim=1)
      else:
        outs=torch.cat([prev_input, outs[:,:-1]], dim=1)
      #print("next input shape: ", outs.shape)
      prev_input=outs
      trg_mask= self.create_mask(outs).cuda()
      tgt_emb = (self.emb_layer_tgt(outs)).cuda()
      tgt_emb = self.positional_encoding_tgt(tgt_emb).cuda()
      length+=1
      #time.sleep(0.5)
    #print("\ngreedy done\n")
    
    #print(f"greedy failed, accuracy on this eval batch: {((c)/(batch_size))*100.0}")
    return outputs

#losses_train, losses_val_global, greedy_accuracy_array, train_accuracy,train_accuracy_array, val_accuracy_global=[],[], [], [], [], []

def train_epoch(model, optimizer):
    model.train()
    accumulation_var=10.0
    losses = 0
    num_batch=0
    #model=model.to(DEVICE)
    count=-1
    losses_train=[]
    losses_val_global=[]
    train_accuracy_array=[]
    val_accuracy_global=[]
    greedy_accuracy_array=[]
    accuracy_greedy=0.0
    for batch in tqdm(train_data_loader):
        count+=1
        src, tgt = batch[0], batch[1]
        src = src.to(DEVICE)
        tgt = tgt.to(DEVICE)

        #tgt_input = tgt[:, :-1].to(DEVICE)
        #print("shape of source : ", src.shape)
        #print("shape of target : ", tgt.shape)
        #print("shape of target : ", tgt_input.shape)
        #src_mask, src_padding_mask, tgt_mask, tgt_padding_mask = model.create_mask(src, tgt_input)
        #print(f"Shapes before forwarding: {src.shape}, {tgt_input.shape}")
        #print(tgt[:,0:-1].shape)
        logits =  model(src, tgt[:,:-1])
        #print("target input: ", tgt[:,:-1].shape)
        #logits=model.greedy(src)
        #tgt_out = tgt.to(DEVICE)[:,1 :]
        #loss = loss_fn(logits.reshape(-1, logits.shape[-1]), tgt_out.reshape(-1))
        #tgt_out=tgt_out.reshape((tgt_out.size(0)*tgt_out.size(1),1))
        #print("prediction: ", logits.shape)
        #print("tgt out: ", tgt_out.shape)
        #print("output shape ", logits.shape)
        #print("output: ", logits)
        logits=logits.transpose(1,2)
        #print(f"shape of logits: {logits.shape} and shape of tgt: {tgt[:,1:].shape}")
        #print("target out: ", tgt[:,:].shape)
        loss = loss_fn(logits[:, :], tgt[:,1:])
        losses_train.append(loss.item())
        
        losses += loss.item()
        
        #print(" shape of output: ", logits.shape)
        #print(" shape of target output: ", tgt_out.shape)
        #print(" shape of output: ", argmax_out.shape)
        
        loss.backward()
        if(num_batch%200==0):

          loss_val, val_accuracy, losses_val=evaluate(model)
          losses_val_global.append(loss_val)
          print("\n validation accuracy ", val_accuracy)
          val_accuracy_global.append(val_accuracy)
          num_correct=0
          for i,j in zip(logits, tgt[:, 1:]):
            correct=torch.sum(torch.argmax(i, dim=0)==j)
            if(correct==logits.size(2)):
              num_correct+=1
          train_accuracy=(num_correct/tgt[:, 1:].size(0))*100.0
          print("correct answers in training: ", num_correct, " over ", tgt.size(0))
          #train_accuracy= (torch.sum((torch.argmax(logits,dim=1) == tgt[:,1:]))/(tgt[:,1:].size(0)*tgt[:,1:].size(1)))*100.0
          train_accuracy_array.append(train_accuracy)
          print(f"\n training accuracy {train_accuracy}\n")
          print("batch num : ", num_batch, " loss train: ", loss.item())
          if(val_accuracy>90.0):
            print("accuracy of validation is greater than 90.0, exiting...")
            break
          model.train()
          
          


        if((num_batch+1)%10==0):
          torch.nn.utils.clip_grad_norm_(model.parameters(),0.1)
          optimizer.step()                            
          optimizer.zero_grad()
          
        num_batch+=1
        
        #print("shape of output: ", logits.shape)
        #print("shape prediction: ", logits.shape)
        #print("target shape: ", tgt_out.shape)
        #print(logits[0].shape, "  ", tgt[0].shape)

        if(num_batch%300==0):
          
          _,batch_eval=next(enumerate(valid_data_loader))
          #model.greedy(batch_eval[0], batch_eval[1][:, 1:])
          accuracy_greedy=evaluate_with_greedy(model, batch_eval)
          print("accuracy of the greedy evaluation: ", accuracy_greedy)
          greedy_accuracy_array.append(accuracy_greedy)
          model.train()
          
          #torch.cuda.empty_cache()
          
    return losses_train, losses_val_global, greedy_accuracy_array, train_accuracy_array, val_accuracy_global


def evaluate_with_greedy(model, batch_eval):
    model.eval()
    
    src, tgt = batch_eval[0], batch_eval[1]
    src = src.to(DEVICE)
    tgt = tgt.to(DEVICE)

    #tgt_input = tgt[:, :-1].to(DEVICE)

    #logits =  model(src, tgt[:,:-1])
    logits=model.greedy(src)
    
    #print("shape before trasposing : ", logits.shape)
    logits=logits.transpose(1,2)
    #print("shape after trasposing : ", logits.shape)
   
    loss = loss_fn(logits, tgt[:,1:])
    
    count=0
    
    num_correct=0
    print(" \n example of greedy: \n")
    for i,j in zip(logits, tgt[:, 1:]):
      correct=torch.sum(torch.argmax(i, dim=0)==j)
      if(correct==logits.size(2)):
        num_correct+=1
      i=torch.argmax(i, dim=0)
      if(count%30==0):
        
        for char_pred, char_tgt in zip(i,j):
          #print(char_pred)
          #print(char_tgt)
          print("target: ", tgt_vocab.id_to_string[char_tgt.item()])
          print("predicted: ", tgt_vocab.id_to_string[char_pred.item()])
        print("")

      count+=1
    
    accuracy=(num_correct/tgt[:, 1:].size(0))*100.0
    print("correct answers in greedy: ", num_correct, " over ", tgt.size(0))
    print("accuracy of greedy: ", accuracy)
    return accuracy

def evaluate(model):
    model.eval()
    losses = 0
    num_batch=0
    #model=model.to(DEVICE)
    loss_val=0
    accumulation_var=10.0
    losses_val=[]
    for _,batch in enumerate(valid_data_loader):
        src, tgt = batch[0], batch[1]
        src = src.to(DEVICE)
        tgt = tgt.to(DEVICE)

        tgt_input = tgt[:, :-1].to(DEVICE)
        tgt_out=tgt[:, 1:].to(DEVICE)
        #tgt_mask, tgt_padding_mask = model.create_mask( src,tgt_input)

        logits =  model(src, tgt_input)
        
        #model(src, tgt_input, src_mask=None, tgt_mask=tgt_mask, src_key_padding_mask=None, tgt_key_padding_mask=tgt_padding_mask)
        
        num_batch+=1
        logits=logits.transpose(1,2)
        loss_val = loss_fn(logits, tgt_out)
        
        losses += loss_val.item()
        #print(logits.shape)
        #logits=torch.argmax(logits, dim=2)

        num_correct=0
        if((num_batch+1)%100==0):
          for i,j in zip(logits, tgt[:, 1:]):
            correct=torch.sum(torch.argmax(i, dim=0)==j)
            if(correct==logits.size(2)):
              num_correct+=1
          accuracy=(num_correct/tgt[:, 1:].size(0))*100.0
          print("correct answers in validation: ", num_correct, " over ", tgt.size(0))
          
          #accuracy_greedy=model.greedy(src)
          #print(accuracy_greedy)
          losses_val.append(loss_val)
          print("\n batch eval num : ", num_batch, " loss val: ", loss_val.item())
          if(accuracy>90.0):
            print("90.0 % of accuracy of validation reached, exiting \n ")
            break


    return (losses / len(valid_data_loader)), accuracy, losses_val

loss_fn = torch.nn.CrossEntropyLoss().cuda()
NUM_EPOCHS = 3

DEVICE='cuda:0'

SRC_VOCAB_SIZE = len(src_vocab)
TGT_VOCAB_SIZE = len(tgt_vocab)
EMB_SIZE = 256
NHEAD = 8
FFN_HID_DIM = 1024
BATCH_SIZE = 64
NUM_ENCODER_LAYERS = 3
NUM_DECODER_LAYERS = 2
# args: src_vocab, trg_vocab, d_model, num_enc_layers, num_dec_layers, nhead,hidden_size, dim_forwards)
transformer = MyTransformer(src_vocab=SRC_VOCAB_SIZE, trg_vocab=TGT_VOCAB_SIZE, d_model=EMB_SIZE,num_enc_layers=NUM_ENCODER_LAYERS , num_dec_layers=NUM_DECODER_LAYERS, nhead=NHEAD,hidden_size=256, dim_forwards=FFN_HID_DIM)

transformer = transformer.to(DEVICE)
optimizer = torch.optim.Adam(transformer.parameters(), lr=1e-4)

#tensor_example=torch.full((64,2,256), 1)
#mask_example=transformer.create_mask(tensor_example)
#print("example tensor \n", mask_example)

NUM_EPOCHS=1
for epoch in range(1, NUM_EPOCHS+1):
    start_time = time.time()
    losses_train, losses_val_global, greedy_accuracy_array, train_accuracy, val_accuracy_global = train_epoch(transformer, optimizer)
    end_time = time.time()
    #val_loss = evaluate(transformer)
    #print((f"Epoch: {epoch}, Train loss: {train_loss:.3f}, Val loss: {val_loss:.3f}, "f"Epoch time = {(end_time - start_time):.3f}s"))

print(losses_train)
print((losses_val_global))
print(val_accuracy_global)
print(greedy_accuracy_array)


new_loss_train=[]
for i in range(len(losses_train)):
  if(i%200==0):
    new_loss_train.append(losses_train[i])
print(len(new_loss_train))

#after 4:21 minutes==> reached 90.0 accuracy

import matplotlib.pyplot as plt
import numpy as np

fig, ax=plt.subplots(nrows=2, ncols=1, figsize=(12,12))

ax[0].plot(np.arange(0,len(new_loss_train)*200, 200),new_loss_train, color="red" , label="Training Loss")
ax[0].plot(np.arange(0,len(losses_val_global)*200,200),losses_val_global, color="blue", label="Validation Loss" )
ax[0].set_xlabel("Batches")
ax[0].set_ylabel("Loss")
ax[0].legend()


ax[1].plot(np.arange(0, len(train_accuracy)*200, 200), train_accuracy, color="red", label="Training Accuracy")
ax[1].plot(np.arange(0, len(val_accuracy_global)*200, 200), val_accuracy_global, color="blue", label="Validation Accuracy")
ax[1].set_xlabel("Batches")
ax[1].set_ylabel("Accuracy")
ax[1].legend()
fig.tight_layout()
plt.show()
fig.savefig('./metrics2.png')

file = open("./losses_train.txt", "w")
file.write(str(losses_train))
file.close()
file = open("./losses_val_global.txt", "w")
file.write(str(losses_val_global))
file.close()
file = open("./val_accuracy_global.txt", "w")
file.write(str(val_accuracy_global))
file.close()
file = open("./greedy_accuracy_array.txt", "w")
file.write(str(greedy_accuracy_array))
file.close()