############################################################
# CMPSC/DS 442: Homework 4 
############################################################

student_name = "Type your full name here."

############################################################
# Imports
############################################################

# Include your imports here, if any are used.

############################################################
# Section 1: Spam Filter ( 50 points )
############################################################

def load_tokens(email_path):
    pass

def log_probs(email_paths, smoothing):
    pass

class SpamFilter(object):

    def __init__(self, spam_dir, ham_dir, smoothing):        
        self.spam_log_probs = 
        self.ham_log_probs = 

        self.p_spam = 
        self.p_ham = 

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
        self.pi = 
        self.a = 
        self.b =  

        pass

    def most_probable_tags(self, tokens):
        pass

    def viterbi_tags(self, tokens):
        pass

