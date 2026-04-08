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

# paths = ["/workspaces/DS442/Assignment4/homework4_data/train/ham/ham%d"%i for i in range(1,11)]
# p = log_probs(paths, 1e-5)
# print(p["the"], p["line"])
# paths = ["/workspaces/DS442/Assignment4/homework4_data/train/spam/spam%d"%i for i in range(1,11)]
# p = log_probs(paths, 1e-5)
# print(p["Credit"], p["<UNK>"])

class SpamFilter(object):

    def __init__(self, spam_dir, ham_dir, smoothing):
        spams = [os.path.join(spam_dir, f) for f in os.listdir(spam_dir)]
        hams = [os.path.join(ham_dir, f) for f in os.listdir(ham_dir)]
        self.spam_log_probs = log_probs(spams, smoothing)
        self.ham_log_probs = log_probs(hams, smoothing)
        nspams = len(spams)
        nhams = len(hams)
        self.p_spam = nspams/(nspams + nhams)
        self.p_ham = nhams/(nspams + nhams)
    
    def is_spam(self, email_path):
        tks = load_tokens(email_path)
        spam_score = math.log(self.p_spam)
        ham_score = math.log(self.p_ham)
        for tk in tks:
            if tk in self.spam_log_probs:
                spam_score += self.spam_log_probs[tk]
            else:
                spam_score += self.spam_log_probs["<UNK>"]
            if tk in self.ham_log_probs:
                ham_score += self.ham_log_probs[tk]
            else:
                ham_score += self.ham_log_probs["<UNK>"]
        return spam_score > ham_score
        
    def most_indicative_spam(self, n):
        common = set(self.spam_log_probs.keys()).intersection(set(self.ham_log_probs.keys()))
        if "<UNK>" in common:
            common.remove("<UNK>")
        word_scores = []
        for w in common:
            expspam = math.exp(self.spam_log_probs[w])
            expham = math.exp(self.ham_log_probs[w])
            pw = expspam*self.p_spam + expham*self.p_ham
            indication_val = self.spam_log_probs[w] - math.log(pw)

            word_scores.append((w, indication_val))

        word_scores.sort(key = lambda x:x[1], reverse=True)
        words = []
        for word, score in word_scores[:n]:
            words.append(word)
        return words

    def most_indicative_ham(self, n):
        common = set(self.spam_log_probs.keys()).intersection(set(self.ham_log_probs.keys()))
        if "<UNK>" in common:
            common.remove("<UNK>")
        word_scores = []
        for w in common:
            expspam = math.exp(self.spam_log_probs[w])
            expham = math.exp(self.ham_log_probs[w])
            pw = expspam*self.p_spam + expham*self.p_ham
            indication_val = self.ham_log_probs[w] - math.log(pw)

            word_scores.append((w, indication_val))

        word_scores.sort(key = lambda x:x[1], reverse=True)
        words = []
        for word, score in word_scores[:n]:
            words.append(word)
        return words


# SPAMTRAINPATH = "/workspaces/DS442/Assignment4/homework4_data/train/spam/"
# HAMTRAINPATH = "/workspaces/DS442/Assignment4/homework4_data/train/ham/"
# SPAMDEVPATH = "/workspaces/DS442/Assignment4/homework4_data/dev/spam/"
# HAMDEVPATH = "/workspaces/DS442/Assignment4/homework4_data/dev/ham/"
# sf = SpamFilter(SPAMTRAINPATH,HAMTRAINPATH, 1e-5)
# # print(sf.is_spam(SPAMTRAINPATH+"/spam1"),sf.is_spam(SPAMTRAINPATH+"/spam2"))
# # print(sf.is_spam(HAMTRAINPATH+"/ham1"),sf.is_spam(HAMTRAINPATH+"/ham2"))
# print(sf.most_indicative_spam(5), sf.most_indicative_ham(5))


############################################################
# Section 2: Hidden Markov Models ( 50 points )
############################################################

def load_corpus(path):
    with open(path, 'r', encoding = "utf-8") as f:

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

