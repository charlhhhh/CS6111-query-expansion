import sys
import nltk
from nltk.tokenize import word_tokenize
import numpy as np
import re
from googleapiclient.discovery import build
nltk.download('punkt')

# Get the google custom search results
def google_custom_search(google_api_key, google_engine_id, query):
    service = build("customsearch", "v1", developerKey=google_api_key)
    res = service.cse().list(q=query, cx=google_engine_id).execute()
    return res

# Function to print the initial information
def print_initial_info(google_api_key, google_engine_id,
                         query, precision):
    print('Parameters:')
    print(f'Client key  = {google_api_key}')
    print(f'Engine key  = {google_engine_id}')
    print(f'Query       = {query}')
    print(f'Precision   = {precision}')
    print('Google Search Results:')
    print('======================')

# Function to print when precision is equal or larger to tar_precision
def print_feedback_achieve (precision, query):
    print("======================")
    print("FEEDBACK SUMMARY")
    print(f"Query {query}")
    print(f"Precision {precision}")
    print("Desired precision reached, done")

# Function to print when precision is smaller than target
def print_precision_smaller_than_tar(tar_precision, google_api_key, google_engine_id, precision, query, aug1, aug2):
    print("======================")
    print("FEEDBACK SUMMARY")
    print(f"Query {query}")
    print(f"Precision {precision}")
    print(f"Still below the desired precision of {tar_precision}")
    print("Indexing results ....")
    print("Indexing results ....")
    print("Augmenting by " + aug1 + ' ' + aug2)
    print('Parameters:')
    print(f'Client key  = {google_api_key}')
    print(f'Engine key  = {google_engine_id}')
    print("Query       = "+ query +' '+ aug1 + ' ' + aug2)
    print(f'Precision   = {tar_precision}')
    print("Google Search Results:\n======================")


# Function to print when precision equals to 0
def print_precision_equal_zero(tar_precision, query):
    print("======================")
    print("FEEDBACK SUMMARY")
    print(f"Query {query}")
    print("Precision 0.0")
    print(f"Still below the desired precision of {tar_precision}")
    print("Indexing results ....")
    print("Indexing results ....")
    print("Augmenting by ")
    print("Below desired precision, but can no longer augment the query")

# Function to get a list of stopwords
def stop_word():
    with open("proj1-stop.txt") as f:
        words = f.readlines()
    words = [x.strip() for x in words]
    return words

'''
basic idea for query expansion:
extract string from title and summary
stopword elimination
calculate some sort of tfidf
further filter down to 2 words
add and reorder the query
'''

def main():

    # To correct the argument
    if not (sys.argv[3].replace('.', '', 1).isdigit() and len(sys.argv) == 5):
        sys.exit(f"Usage: {sys.argv[0]} [Google API Key] [Google Engine ID] [Precision] [Query]")

    # Set the initial values
    google_api_key = sys.argv[1]
    google_engine_id = sys.argv[2]
    query = sys.argv[4]
    tar_precision = float(sys.argv[3])
    
    # Print initial information
    print_initial_info(google_api_key, google_engine_id, query, tar_precision)

    # Initialize precision
    precision = 0
    
    
    
    # If the first iteration there are no relevant results among the top-10 pages that Google returns 
    # (i.e., precision@10 is zero), then program should simply terminate
    
    stopwords = stop_word()
    
    while precision <= tar_precision:
        # Get Google Custom Search Result
        results = google_custom_search(google_api_key, google_engine_id, query)
        total_results = int(results['searchInformation']['totalResults'])
        if total_results < 10:
            sys.exit()
        count_relevant = 0 # relevant html files
        count_html = 0 # total html files
        contents = [] # store the title and summary of query results as list of lists
        for i, item in enumerate(results['items'][:10]):
            snip = 'None'
            print(f"Result {i + 1}")
            print('[')
            print(f" URL: {item['link']}")
            print(f" Title: {item['title']}")
            # Check if 'snippet' key exists before trying to access it
            if 'snippet' in item:
                snip = item['snippet']
                print(f" Summary: {snip}")
            else:
                print(" Summary: No summary available.")
            print(']')
            print()
            
            # If HTML file, then count_html++
            if "fileFormat"  not in item:
                count_html += 1

            feedback = input('Relevant (Y/N)?')

            # interpreting both upper case and lowercase responses, and count_relevant++
            if (feedback.lower() == 'y' or feedback.lower() == 'yes') and "fileFormat"  not in item:
                count_relevant += 1
                # only store relevant query result
                content_i = item['title'] + ' ' + snip
                # use full lower case
                content_i = content_i.lower()
                # remove nonalphanumeric
                content_i = re.sub(r'[^A-Za-z0-9 ]+', '', content_i)
                # remove \xa0
                content_i = re.sub('\xa0', ' ', content_i)
                # stopword elimination
                # ref: https://www.geeksforgeeks.org/removing-stop-words-nltk-python/
                content_tok = word_tokenize(content_i)
                
                #content_tok = list(set(content_tok))
                content_i = [w for w in content_tok if not w.lower() in stopwords]
                contents.append(content_i)

        precision = count_relevant / count_html if count_html else 0
         
        # If precision equals to 0, just exit with message
        if precision == 0:
            print_precision_equal_zero(tar_precision, query)
            break
        # If precision equals or larger to tar_precision, exit with success message
        elif precision >= tar_precision:
            
            print_feedback_achieve(precision, query)
            break
        else: # when precision is lower than threshold
            # find most frequent words in contents
            freq = {}
            for s in contents: # in each search result
                for word in s: # scan through each word in the search result
                    if word not in freq:
                        freq[word] = 1
                    else: 
                        freq[word] += 1
            # ref: https://www.freecodecamp.org/news/sort-dictionary-by-value-in-python/
            sorted_freq = sorted(freq.items(), key=lambda x:x[1], reverse=True)
            most_freqs = list(dict(sorted_freq).keys()) # extract the most frequent keywords, dedscending order
            most_freq = [] # store the two most freq 
            for w in most_freqs:
                if w not in query: # ensure the same words dont get added to the query twice
                    most_freq.append(w)
                    if len(most_freq) == 2:
                        break
            #update query
            
            print_precision_smaller_than_tar(tar_precision, google_api_key, google_engine_id, precision, query, most_freq[0],most_freq[1])
            query = query + ' ' + most_freq[0] + ' ' + most_freq[1]

if __name__ == "__main__":
    main()
