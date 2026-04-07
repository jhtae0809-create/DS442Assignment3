############################################################
# CMPSC/DS 442: Homework 4 
############################################################

student_name = "Hyuntae Jeong"

############################################################
# Imports
import email
import collections
import math
import os

############################################################

# Include your imports here, if any are used.

############################################################
# Section 1: Spam Filter ( 50 points )
############################################################

def load_tokens(email_path):
    with open(email_path, 'r', encoding = "utf-8") as f:
        msg = email.message_from_file(f)
    tks = []
    for l in email.iterators.body_line_iterator(msg):
        tks.extend(l.split())
    return tks

# ham_dir = "/workspaces/DS442/Assignment4/homework4_data/train/ham/"
# print(load_tokens(ham_dir+"ham1")[200:204])
# print(load_tokens(ham_dir+"ham2")[110:114])
# spam_dir = "/workspaces/DS442/Assignment4/homework4_data/train/spam/"
# print(load_tokens(spam_dir+"spam1")[1:5])
# print(load_tokens(spam_dir+"spam2")[:4])

def log_probs(email_paths, smoothing):
    allt = []
    for path in email_paths:
        tokens = load_tokens(path)
        allt+=tokens
    word_counts = collections.Counter(allt)
    wtotal=sum(word_counts.values())
    vsize=len(word_counts)
    denom = wtotal + smoothing * (vsize+1)
    log_prob={}
    for k, v in word_counts.items():
        log_prob[k] = math.log((v+smoothing)/denom)
    log_prob["<UNK>"] = math.log(smoothing/denom)
    return log_prob

paths = ["/workspaces/DS442/Assignment4/homework4_data/train/ham/ham%d"%i for i in range(1,11)]
p = log_probs(paths, 1e-5)
print(p["the"], p["line"])
paths = ["/workspaces/DS442/Assignment4/homework4_data/train/spam/spam%d"%i for i in range(1,11)]
p = log_probs(paths, 1e-5)
print(p["Credit"], p["<UNK>"])

class SpamFilter(object):

    def __init__(self, spam_dir, ham_dir, smoothing):        
        self.spam_log_probs = None
        self.ham_log_probs = None
        self.p_spam = None
        self.p_ham = None

        pass
    
    def is_spam(self, email_path):
        pass

    def most_indicative_spam(self, n):
        pass

    def most_indicative_ham(self, n):
        pass


############################################################
# Section 2: Hidden Markov Models ( 50 points )
############################################################

def load_corpus(path):
    pass

class Tagger(object):

    def __init__(self, sentences):
        self.pi = None
        self.a = None
        self.b =  None

        pass

    def most_probable_tags(self, tokens):
        pass

    def viterbi_tags(self, tokens):
        pass

