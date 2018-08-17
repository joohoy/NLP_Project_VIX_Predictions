import torch
import torch.utils.data as tud
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from collections import Counter, defaultdict
import operator
import os, math
import numpy as np
import random
import copy
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import KFold
from sklearn.model_selection import LeaveOneOut
#os.chdir("C:\\Users\\jooho\\NLPProject")
os.chdir("C:\\Users\\dabel\\Documents\\Natural_Language_Processing_MPCS\\project")

POS_LABEL = 1
NEG_LABEL = -1
NONE_LABEL = 0   

def load_data():
    """Load all necessary data"""
    df = pd.read_pickle("all_data.pickle")
    return df

def tokenize_doc(statement):
    """
    Tokenize a document and return its bag-of-words representation.
    doc - a string representing a document.
    returns a dictionary mapping each word to the number of times it appears in doc.
    """
    c = defaultdict(float)
    for word in statement:
        c[word] += 1
    return c

class NaiveBayes():
    """A Naive Bayes model for text classification."""
    def __init__(self, statements, labels, alpha):
        self.vocab = Counter([word for content in statements for word in content])
        self.word_to_idx = {k: v+1 for v, k in enumerate(self.vocab)} # word to index mapping
        self.word_to_idx["UNK"] = 0 # all the unknown words will be mapped to index 0
        self.idx_to_word = {v:k for k, v in self.word_to_idx.items()}
        self.label_to_idx = {POS_LABEL: 0, NEG_LABEL: 1, NONE_LABEL: 2}
        self.idx_to_label = [POS_LABEL, NEG_LABEL, NONE_LABEL]
        self.vocab = set(self.word_to_idx.keys())
        # a smoothing parameter
        self.alpha = alpha
        # class_total_doc_counts is a dictionary that maps a class (i.e., pos/neg) to
        # the number of documents in the trainning set of that class
        self.class_total_doc_counts = { POS_LABEL: 0.0,
                                        NEG_LABEL: 0.0,
                                        NONE_LABEL: 0.0}

        # class_total_word_counts is a dictionary that maps a class (i.e., pos/neg) to
        # the number of words in the training set in documents of that class
        self.class_total_word_counts = { POS_LABEL: 0.0,
                                         NEG_LABEL: 0.0,
                                         NONE_LABEL: 0.0}

        # class_word_counts is a dictionary of dictionaries. It maps a class (i.e.,
        # pos/neg) to a dictionary of word counts. For example:
        #    self.class_word_counts[POS_LABEL]['good']
        # stores the number of times the word 'good' appears in documents
        # of the positive class in the training documents.
        self.class_word_counts = { POS_LABEL: defaultdict(float),
                                   NEG_LABEL: defaultdict(float),
                                   NONE_LABEL: defaultdict(float)}


    def train_model(self, statements, labels):
        """
        This function processes the entire training set one document at a time.   
        It makes use of the tokenize_doc and update_model functions you will implement.
        After the training is done, it prints the model statistics. 
        """
        for i in range(len(statements)):
            self.tokenize_and_update_model(statements[i], labels[i])
        #self.report_statistics_after_training()

    def report_statistics_after_training(self):
        """
        Report a number of statistics after training.
        """

        print("REPORTING CORPUS STATISTICS")
        print("NUMBER OF DOCUMENTS IN POSITIVE CLASS:", self.class_total_doc_counts[POS_LABEL])
        print("NUMBER OF DOCUMENTS IN NEGATIVE CLASS:", self.class_total_doc_counts[NEG_LABEL])
        print("NUMBER OF DOCUMENTS IN NONE CLASS:", self.class_total_doc_counts[NONE_LABEL])
        print("NUMBER OF TOKENS IN POSITIVE CLASS:", self.class_total_word_counts[POS_LABEL])
        print("NUMBER OF TOKENS IN NEGATIVE CLASS:", self.class_total_word_counts[NEG_LABEL])
        print("NUMBER OF TOKENS IN NONE CLASS:", self.class_total_word_counts[NONE_LABEL])
        print("VOCABULARY SIZE: NUMBER OF UNIQUE WORDTYPES IN TRAINING CORPUS:", len(self.vocab))

    def update_model(self, bow, label):
        """
        Update internal statistics given a document represented as a bag-of-words
        bow - a map from words to their counts
        label - the class of the document whose bag-of-words representation was input
        This function doesn't return anything but should update a number of internal
        statistics. Specifically, it updates:
          - the internal map the counts, per class, how many times each word was
            seen (self.class_word_counts)
          - the number of words seen for each class (self.class_total_word_counts)
          - the vocabulary seen so far (self.vocab)
          - the number of documents seen of each class (self.class_total_doc_counts)
        """
        for word in bow.keys():
            self.class_word_counts[label][word] += bow[word]
        self.class_total_word_counts[label] += sum(bow.values())
        self.class_total_doc_counts[label] += 1
        return 
        
    def tokenize_and_update_model(self, doc, label):
        """
        Tokenizes a document doc and updates internal count statistics.
        doc - a string representing a document.
        label - the sentiment of the document (either postive or negative)

        Make sure to tokenize all of the tokens to lower case!
        """

        bow = tokenize_doc(doc)
        self.update_model(bow, label)

    def top_n(self, label, n):
        """
        Returns the most frequent n tokens for documents with class 'label'.
        """
        s = sorted(self.class_word_counts[label].items(), key=lambda t: t[1], reverse = True)
        return s[0:n]

    def p_word_given_label(self, word, label):
        """
        Returns the probability of word given label (i.e., P(word|label))
        according to this NB model.
        """
        count_in_label= self.class_word_counts[label][word]
        all_in_label = self.class_total_word_counts[label]
        return (count_in_label/all_in_label)
        
    def p_word_given_label_and_psuedocount(self, word, label):
        """
        Returns the probability of word given label wrt psuedo counts.
        The pseudo counts is defined as "word count + alpha", where alpha is a parameter to adjust the word count. 
        After such adjustment, the word probability will be "word pseudo count / sum of all words pseudo count" 
        for a single word of a class. 
        """
        count_in_label= self.class_word_counts[label][word]
        all_in_label = self.class_total_word_counts[label]
        return (count_in_label + self.alpha)/(all_in_label + (len(self.vocab)*self.alpha))
        
    def log_likelihood(self, bow, label):
        """
        Computes the log likelihood of a set of words give a label and psuedocount.
        bow - a bag of words (i.e., a tokenized document)
        label - either the positive or negative label
        """
        log_probs = [np.log(self.p_word_given_label_and_psuedocount(word, label)) for word in bow.keys()]
        return sum(log_probs)
        
    def log_prior(self, label):
        """
        Returns a float representing the fraction of training documents
        that are of class 'label'.
        """
        prior = self.class_total_doc_counts[label] / sum(self.class_total_doc_counts.values())
        return np.log(prior)
        
    def unnormalized_log_posterior(self, bow, label):
        """
        bow - a bag of words (i.e., a tokenized document)
        Computes the unnormalized log posterior (of doc being of class 'label').
        Think about what is the posterior probability of a document given a label by bayes rule. 
        As the denominator is a constant for all classes, you don't need to divide by that constant, 
        and we call it "unnormalized". 
        """
        return self.log_prior(label) + self.log_likelihood(bow, label)
        
    def classify(self, bow):
        """
        bow - a bag of words (i.e., a tokenized document)

        Compares the unnormalized log posterior for doc for both the positive
        and negative classes and returns the either POS_LABEL or NEG_LABEL
        (depending on which resulted in the higher unnormalized log posterior).
        """
        pos_log_post = self.unnormalized_log_posterior(bow, POS_LABEL)
        neg_log_post = self.unnormalized_log_posterior(bow, NEG_LABEL)
        none_log_post = self.unnormalized_log_posterior(bow, NONE_LABEL)
        if np.max([pos_log_post,neg_log_post,none_log_post]) == pos_log_post:
            return POS_LABEL
        elif np.max([pos_log_post,neg_log_post,none_log_post]) == neg_log_post:
            return NEG_LABEL
        else:
            return NONE_LABEL
        
    def likelihood_log_ratio(self, word, label):
        """
        Returns the ratio of P(word|label ) to P(word|not label).
        """
        if label == POS_LABEL:
            ratio = self.p_word_given_label_and_psuedocount(word, POS_LABEL) / ( self.p_word_given_label_and_psuedocount(word, NONE_LABEL) + self.p_word_given_label_and_psuedocount(word, NEG_LABEL))
        if label == NEG_LABEL:
            ratio = self.p_word_given_label_and_psuedocount(word, NEG_LABEL) / ( self.p_word_given_label_and_psuedocount(word, NONE_LABEL) + self.p_word_given_label_and_psuedocount(word, POS_LABEL))
        if label == NONE_LABEL:
            ratio = self.p_word_given_label_and_psuedocount(word, NONE_LABEL) / ( self.p_word_given_label_and_psuedocount(word, POS_LABEL) + self.p_word_given_label_and_psuedocount(word, NEG_LABEL))
        return np.log(ratio)
        
    def evaluate_classifier_accuracy(self, statements, labels):
        """
        This function should go through the test data, classify each instance and
        compute the accuracy of the classifier (the fraction of classifications
        the classifier gets right.
        """
        accuracy = []
        for i in range(len(statements)):
            label = labels[i]
            bow = tokenize_doc(statements[i])
            predicted = self.classify(bow)
            if predicted == label:
                accuracy.append(1.0)
            else:
                accuracy.append(0.0)
        return sum(accuracy)/float(len(accuracy))

def make_train_test_data(df, label, test_size = 0.2):
    """Divide data into train and test data for model training and validating."""
    X = df.statements
    y = df[label]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = test_size)#, random_state=42)
    return X_train, X_test, y_train, y_test


def param_fitting(train_data,train_labels):
    """
    This function takes the training data/labels and returns best performing alpha parameter.
    Use 5 fold cross validation to hypertune the parameter.
    """
    #x = np.arange(.05,2.05,.05)
    x = [.0001,.0005, .001, .005, .01, .05, .1, .5, 1, 5, 10,50,100]
    scores = []
    kf = KFold(n_splits = 5)
    for alpha in x:
        kfold_scores = []
        for train, test in kf.split(train_data):
            nb_model = NaiveBayes(train_data[train],train_labels[train], alpha)
            nb_model.train_model(train_data[train], train_labels[train])
            kfold_scores.append(nb_model.evaluate_classifier_accuracy(train_data[test], train_labels[test]))
        scores.append(np.mean(kfold_scores))      
    return x[np.argmax(scores)]    

def print_top_words(ll1, ll2, ll3, num = 5):
    labels = ['vix_buckets_1d', 'vix_buckets_5d', 'tnx_buckets_1d', 'tnx_buckets_5d']
    for label in labels:
        pos = sorted(ll1[label].items(), key=lambda t: t[1], reverse = True)
        neg = sorted(ll2[label].items(), key=lambda t: t[1], reverse = True)
        none = sorted(ll3[label].items(), key=lambda t: t[1], reverse = True)
        print(f'Top {num} positive words for {label} =')
        print([i[0] for i in pos[0:num]])
        print(f'Top {num} negative words for {label} =')
        print([i[0] for i in neg[0:num]])
        print(f'Top {num} neutral words for {label} = ')
        print([i[0] for i in none[0:num]])        
        print()


def main(df):
    """ Driver function that trains a model for each label """

    labels = ['vix_buckets_1d', 'vix_buckets_5d', 'tnx_buckets_1d', 'tnx_buckets_5d']
    scores = []
    for label in labels:
        train_data, test_data, train_labels, test_labels = make_train_test_data(df, label) 
        #alpha = param_fitting(train_data, train_labels)
        alpha = 1
        nb_model = NaiveBayes(train_data,train_labels, alpha)
        nb_model.train_model(train_data, train_labels)
        score = nb_model.evaluate_classifier_accuracy(test_data, test_labels)
        print(f"Score for {label} = {score}")
        scores.append(score)
        print(log_lik_pos[label]['bias'])
        for word in nb_model.vocab:
            log_lik_pos[label][word] += nb_model.likelihood_log_ratio(word, POS_LABEL)
            log_lik_neg[label][word] += nb_model.likelihood_log_ratio(word, NEG_LABEL)
            log_lik_none[label][word] += nb_model.likelihood_log_ratio(word, NONE_LABEL)
        print(type(nb_model.likelihood_log_ratio('bias', POS_LABEL)))     
        print(log_lik_pos[label]['bias'])
    return scores  
    ##

if __name__ == '__main__':
    """ Due to the random component and lack of data we want to run it multiple
    times and average the scores.
    """
    NUM_EPOCHS = 4
    df = load_data()
    all_scores = []
    log_lik_pos = {'vix_buckets_1d' : defaultdict(np.float64), 'vix_buckets_5d': defaultdict(np.float64),
                   'tnx_buckets_1d': defaultdict(np.float64), 'tnx_buckets_5d': defaultdict(np.float64)}
    log_lik_neg = {'vix_buckets_1d' : defaultdict(np.float64), 'vix_buckets_5d': defaultdict(np.float64),
                   'tnx_buckets_1d': defaultdict(np.float64), 'tnx_buckets_5d': defaultdict(np.float64)}
    log_lik_none = {'vix_buckets_1d' : defaultdict(np.float64), 'vix_buckets_5d': defaultdict(np.float64),
                   'tnx_buckets_1d': defaultdict(np.float64), 'tnx_buckets_5d': defaultdict(np.float64)}
    for i in range(NUM_EPOCHS):
        print(i)
        scores = main(df)
        all_scores.append(scores)
    all_scores = np.array(all_scores)    
    print()
    print("Average score for each independent variable = ")
    print(np.mean(all_scores,axis= 0))
    print()
    print_top_words(log_lik_pos,log_lik_neg,log_lik_none, 5)
    



