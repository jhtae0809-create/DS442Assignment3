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
        res =[]
        for line in f.readlines():
            tkline = line.strip().split()
            res.append([tuple(tk.rsplit("=",1)) for tk in tkline])
    return res

# c = load_corpus("/workspaces/DS442/Assignment4/brown_corpus.txt")
# print(c[1799])

class Tagger(object):

    def __init__(self, sentences):
        tagcounts = collections.defaultdict(int)
        starttag = collections.defaultdict(int)
        transition = collections.defaultdict(lambda: collections.defaultdict(int))
        emission = collections.defaultdict(lambda: collections.defaultdict(int))
        vocab=set()
        tags=set()
        num_sc = len(sentences)
        for sc in sentences:
            if not sc:
                continue
            first_tag=sc[0][1]
            starttag[first_tag] +=1
            for i in range(len(sc)):
                tk, tag=sc[i]
                tagcounts[tag]+=1
                vocab.add(tk)
                tags.add(tag)
                emission[tag][tk]+=1
                if i < len(sc)-1:
                    nexttag=sc[i+1][1]
                    transition[tag][nexttag]+=1
        a = 1e-5
        ntags = len(tags)
        nvocab = len(vocab)

        self.pi = {}
        self.a = {}
        self.b =  {}

        for tag in tags:
            self.pi[tag] = (starttag[tag]+a)/(num_sc + a*ntags)

        for i in tags:
            self.a[i]={}
            self.b[i]={}
            emiss_denom = tagcounts[i]
            unk_prob = a / (emiss_denom + a * (nvocab + 1))
            self.b[i]["<UNK>"] = unk_prob
            trans_denom = sum(transition[i].values())
            for j in tags:
                self.a[i][j] = (transition[i][j] + a) / (trans_denom + a * ntags)
            for w, count in emission[i].items():
                self.b[i][w] = (count+a)/(emiss_denom + a *(nvocab+1))

        

    def most_probable_tags(self, tokens):
        resulttags=[]
        for tk in tokens:
            besttag = None
            max_p = -100
            for t in self.b.keys():
                p = self.b[t].get(tk,self.b[t]["<UNK>"])
                if p>max_p:
                    max_p=p
                    besttag=t
            resulttags.append(besttag)
        return resulttags


    def viterbi_tags(self, tokens):
        if not tokens:
            return []
        n = len(tokens)
        tags = list(self.pi.keys())
        B = [{} for _ in range(n)]
        V = [{} for _ in range(n)]
        w0 = tokens[0]
        for t in tags:
            ppi = self.pi[t]
            pb = self.b[t].get(w0, self.b[t]["<UNK>"])
            B[0][t]=None
            V[0][t]=math.log(ppi) + math.log(pb)
        for i in range(1,n):
            wi = tokens[i]
            for curr in tags:
                maxp = -10*100
                bestpt = None
                pb = self.b[curr].get(wi, self.b[curr]["<UNK>"])
                logb=math.log(pb)
                for prev in tags:
                    pa = self.a[prev][curr]
                    path_prob = V[i-1][prev] + math.log(pa)+logb
                    if path_prob > maxp:
                        maxp = path_prob
                        bestpt=prev
                V[i][curr] = maxp
                B[i][curr] = bestpt
        bestlasttag = max(V[n-1].keys(), key=lambda x:V[n-1][x])
        best_path = [bestlasttag]
        currp = bestlasttag
        for t in range(n-1, 0, -1):
            currp = B[t][currp]
            best_path.append(currp)
        return best_path[::-1]
                
        
        


# c = load_corpus("/workspaces/DS442/Assignment4/brown_corpus.txt")
# t = Tagger(c)
# print(t.most_probable_tags(["The", "man", "walks", "."]))
# print(t.most_probable_tags(["The", "blue", "bird", "sings"]))
# #s="I am waiting to reply".split()
# s="I saw the play".split()
# print(t.most_probable_tags(s))
# print(t.viterbi_tags(s))
