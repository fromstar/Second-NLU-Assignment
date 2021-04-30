import spacy
import os
import pandas as pd
from sklearn.metrics import classification_report
from conll import *
from spacy.tokens import Span

#------------EX.1----------------
def get_sentences(path): #Function that returns all the sentences in the file .txt and the corpus
  text = ''
  sents = []
  nlp = spacy.load('en_core_web_sm')
  corpus = read_corpus_conll(path)[1:]
  for sentence in corpus:
    for token in sentence:
      text += token[0].split()[0] + " " #take only the text of the token
    sents.append(nlp(text))
    text = ''
  return sents,corpus

def spacytoconll(sents): #convert the spacy ent_type in the conll format
  for doc in sents:
    for t in doc:
      if t.ent_type_ == "GPE":
        t.ent_type_ = "LOC"
      elif t.ent_type_ == "FAC":
        t.ent_type_ = "LOC"
      elif t.ent_type_ == "PERSON":
        t.ent_type_ = "PER"
      elif t.ent_type_ == "ORG":
        t.ent_type_ = "ORG"
      elif t.ent_type_ == "":
        t.ent_type_ = ""
      else:
        t.ent_type_ = "MISC"

def align_entities(doc): # function that return a list of tuples with the merged tokens and their ent_ion+ent_type
  merged_tokens = []     # to pass next in the evaluate function
  txt = ''
  for t in doc:
    txt += t.text
    if t.whitespace_ == ' ':
      if t.ent_type_ != '':
        merged_tokens.append((txt,t.ent_iob_+"-"+t.ent_type_))
      else:
        merged_tokens.append((txt,t.ent_iob_))
      txt = ''
  return merged_tokens
      
def token_level_performance(path):
  sents,corpus = get_sentences(path)
  spacytoconll(sents)

  index_sents = []
  index_corpus = []

  ref  = []
  hyp = []
  for i in range(len(sents)):
    hyp.append(align_entities(sents[i])) #append all the tuple for the conll.py evaluate function

  for snt in hyp:
    for ent in snt: 
      index_sents.append(ent[1]) #append all the spacy tag in a 1d list.
  for sentence in corpus:
    ents_sentence = []
    for t in sentence:
      index_corpus.append(t[0].split()[3]) #append al the corpus tag in a 1d list.
      ents_sentence.append((t[0].split()[0],t[0].split()[3]))
    ref.append(ents_sentence)#appent a tuple with ent text and the tag for the evaluate function 
  
  results = classification_report(index_sents,index_corpus)
  print("Token-level performance:")
  print(results)

  results = evaluate(ref, hyp)

  pd_tbl = pd.DataFrame().from_dict(results, orient='index')
  pd_tbl.round(decimals=3)
  pd_tbl.style
  print("CoNLL chunk-level performance:")
  print(pd_tbl)

#------------EX.2----------------
def group_entities(sentence): #function that for each chunk groups the various ent_type in a list of list
  nlp = spacy.load('en_core_web_sm')
  doc = nlp(sentence)
  group_ents = []
  group = []
  for chunk in doc.noun_chunks:
    for t in chunk:
      if t.ent_type_ != '' and not t.ent_type_ in group:
        group.append(t.ent_type_)
    group_ents.append(group.copy())
    group.clear()
  
  is_chunk = False #if a token is not recognized I append it's ent_type at the end of the list. Since i have only to count
  for token in doc:#the frequency combination I don't care if they are ordered.
    for chunk in doc.noun_chunks:
      for t in chunk:
        if t.text == token.text:
          is_chunk = True
          break;
    if is_chunk == False and token.ent_type_ != '':
      group_ents.append([token.ent_type_])
    is_chunk = False
  return group_ents

def freq_combination(sentence):
  group_ent = group_entities(sentence) #get the ent_type grouped
  lst_freq = []
  cnts = 0
  for lst_1 in group_ent: #count how many times a combination is presents.
    for lst_2 in group_ent:
      if set(lst_1) == set(lst_2):
        cnts += 1
    if not [lst_1,cnts] in lst_freq: #if I count a combination multiple times, just the first is inserted
      lst_freq.append([lst_1,cnts])
    cnts = 0

  print("Sentence: " + sentence)
  print("Frequency of grouped entites: ")  
  for lst in lst_freq:  
    print("%s: %s"%(lst[0],lst[1]))
        
#------------EX.3----------------
def extend_entity_span(sentence):
  print(sentence)
  nlp = spacy.load('en_core_web_sm')
  doc = nlp(sentence)
  print(doc.ents)
  for ent in doc.ents:
    for token in ent:
      for children in token.children:#checking all the token's children
      #if the child is in the same position of the token before the start of the entity or after the end
      #and is compound it means that it should be part of the entity
        rng = range(ent.start,ent.end)
        if not children.i in rng and children.dep_ == 'compound':
          if children.ent_type_ == '':
            children.ent_type_ = ent.label_
          #setting the new starting and ending points of the entity
          if ent.start < children.i:
            start = ent.start
          else:
            start = children.i
          if ent.end > children.i+1:
            end = ent.end
          else:
            end = children.i+1
          #creating the new entity to substitute to the last entity analyzed
          #doc.ents[list(doc.ents).index(ent)] = Span(doc, start, end, ent.label_)
          lst_doc = list(doc.ents) #To search and replace the entity it's necessary get the doc.ents in a form of list
                                   #because the tuples are immutable.
          index = lst_doc.index(ent)#Get the ent position to replace.
          lst_doc[index] = Span(doc, start, end, ent.label_)
          doc.ents = tuple(lst_doc)           
  print(doc.ents)
  
if __name__ == '__main__':  
  print("Exercise 1\n")
  token_level_performance('conll2003/test.txt')
  print("\nExercise 2\n")
  sentence = 'Apple\'s Steve Jobs died in 2011 in Palo Alto, California.'
  freq_combination(sentence)
  print("\nExercise 3\n")
  extend_entity_span('He said a proposal last month by EU Farm Commissioner Franz Fischler to ban sheep brains')
