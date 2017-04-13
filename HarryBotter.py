import os
import sys, traceback
reload(sys)
sys.setdefaultencoding('utf-8')
import json
import FacebookAPI as FB, NLP

## Resources for querying API and parsing results
import re, collections, json, urllib, urllib2, random

## Resources for performing POS tagging & lamda expressions
from nltk import RegexpParser
from nltk.data import load
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize, sent_tokenize


import requests
from flask import Flask, request, render_template

app = Flask(__name__)
token = os.environ["PAGE_ACCESS_TOKEN"]

WIKIA_API_URL = 'http://www.harrypotter.wikia.com/api/v1'
SEARCH_URI = '/Search/List/?'
ARTICLES_URI = '/Articles/AsSimpleJson?'
QUERY_RESULT_LIMIT = 25
SEARCH_QUERY_TEMPLATE = {'query': '', 'limit': QUERY_RESULT_LIMIT}
ARTICLE_QUERY_TEMPLATE = {'id': ''}

class Intent:
    QUERY = 1
    STATEMENT = 2
    NONSENSE = 3
    DEVIOUS = 4

grammar = r"""
	NP: {<DT|PRP\$>?<JJ|JJS>*<NN|NNS>+}
		{<NNP|NNPS><IN><DT>?<NNP|NNPS>}
		{<NNP|NNPS>+}
		{<PRP>}
		{<JJ>+}
		{<WP|WP\s$|WRB>}
	VP: {<VB|VBD|VBG|VBN|VBP|VBZ|MD><NP>?}
	PP: {<IN><NN|NNS|NNP|NNPS|CD>}
"""
parser = RegexpParser(grammar)

## Pre-defined responses to statements and undecipherable user questions
GREETING = 'I\'m Harry Botter pleasure to meet you.'
RESPONSE_TO_NONSENSE = ['I\'m sorry but that is simply not a question!',"*scratch my head* :(",
                        "How do I respond to that... :O", "I don't know you can ask Hermione... :/",
                        "I can be not-so-smart from time to time... :(",
                        "Err... you know I'm not the real Harry Potter, right? :O",
                        'Is that a real question? Well it\'s not very good now is it?',
                        'Honestly, that is not funny, you\'re lucky I don\'t report you to the headmaster!',
                        'It appears you haven\'t asked a question. How do you expect me to perform any magic without a question?',
                        'I hope you\'re pleased with yourself. Your comments could get us all killed, or worse... expelled!']
SPELLING_ERROR = 'It\'s %s, not %s!'
NO_INFORMATION_AVAILABLE = 'Even \"Hogwarts: A History\" couldn\'t answer that question. Perhaps try a different question.'
RESPONSE_STARTERS = ['', 'Well, ' 'You see, ', 'I know that ', 'I believe that ', 'It is said that ',
                     'To my knowledge, ']

@app.route('/privacy', methods=['GET'])
def privacy():
    return render_template('privacy.html')

@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    sender_id = messaging_event["sender"]["id"]  # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_payload = messaging_event["postback"]["payload"]
                    user = FB.get_user_fb(token,sender_id)
                    print 'Message Payload is '+ str(message_payload)
                    if message_payload == "Harry_Botter_Help":
                        handle_help(sender_id)

                    elif message_payload == "Harry_Botter_Get_Started":
                        handle_first_time_user(sender_id,user)

                    elif message_payload == "Harry_Botter_Characters":
                        handle_characters(sender_id)

                    elif message_payload == "Harry_Botter_Spells":
                        handle_spells(sender_id)

                print 'Messaging Event is '+ str(messaging_event)
                if messaging_event.get("message"):  # someone sent us a message
                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message = messaging_event["message"]  # the message's text
                    user = FB.get_user_fb(token, sender_id)
                    FB.show_typing(token, sender_id)
                    response, images = processIncoming(sender_id, message)
                    if response == 'help':
                        FB.show_typing(token, sender_id, 'typing_off')
                        handle_help(sender_id)
                    elif response == 'characters':
                        FB.show_typing(token, sender_id, 'typing_off')
                        handle_characters(sender_id)
                    elif response == 'spells':
                        FB.show_typing(token, sender_id, 'typing_off')
                        handle_spells(sender_id)
                    elif response == 'places':
                        FB.show_typing(token, sender_id, 'typing_off')
                        handle_help(sender_id)
                    else:
                        FB.show_typing(token, sender_id, 'typing_off')
                        FB.send_message(token, sender_id, response)
                        if images:
                            print 'Images here'+ str(images)
                            FB.send_group_pictures(app,token,sender_id,images)

                return "ok"



    return "ok", 200


def processIncoming(user_id, message):
    try:

        userInput = message['text']
        userInput = userInput.lower()
        user = FB.get_user_fb(token, user_id)
        response =''
        ## TEMP: to see & verify POS tagging
        # print("User Input : %s" % userInput)

        response = ''
        if userInput.lower() == 'help':
            return 'help',[]
        elif userInput.lower() == 'characters' or userInput.lower() == 'character':
            return 'characters',[]
        elif userInput.lower() == 'spells' or userInput.lower() == 'spell':
            return 'spells',[]
        elif userInput.lower() == 'places' or userInput.lower() == 'place':
            return 'places',[]

        if NLP.isAskingBotInformation(userInput):
            return NLP.handleBotInfo(userInput),[]

        if NLP.isGreetings(userInput):
            greeting = "%s %s :D" % (NLP.sayHiTimeZone(user), user['first_name'])
            FB.send_message(token, user_id, greeting)
            return "How can I help you?",[]

        elif NLP.isGoodbye(userInput):
            return NLP.sayByeTimeZone(user),[]

        ## Perform POS-tagging on user input
        tagged_input = pos_tag(word_tokenize(userInput))
        print("POS-Tagged User Input : %s " % tagged_input)
        intent = obtainUserIntent(tagged_input)

        if intent == Intent.QUERY:
            # print("Harry IS THINKING...")
            response,images = deviseAnswer(tagged_input)
        elif intent == Intent.NONSENSE:
            # print("Harry THINKS YOU ARE UNCLEAR.")
            images = []
            response = "%s" % (RESPONSE_TO_NONSENSE[random.randint(0, len(RESPONSE_TO_NONSENSE) - 1)])
    except Exception, e:
        print e
        traceback.print_exc()
        return NLP.oneOf(NLP.error),[]
    return response ,images

## This method takes the POS tagged user input and determines what the intention of the user was
## returns Intent.NONSENSE, Intent.QUERY or Intent.STATEMENT
##
def obtainUserIntent(taggedInput):
    intent = Intent.NONSENSE

    ## If the sentence ends with a question mark or starts with a Wh-pronoun or adverb
    ## then safely assume it is a question
    if isQuestion(taggedInput):
        intent = Intent.QUERY

    return intent

def isQuestion(taggedInput):
    ## Helper Information
    firstWordTag = taggedInput[0][1]
    lastToken = taggedInput[len(taggedInput) - 1][0]
    lastWordTag = taggedInput[len(taggedInput) - 1][1]
    secondLastWordTag = taggedInput[len(taggedInput) - 2][1]

    # If starts or ends with WH, ends with ? or starts with Auxilliary verb -- it is a question
    if firstWordTag.startswith('WP') or (firstWordTag.startswith('WRB') or lastToken == '?'):
        return True
    elif lastWordTag.startswith('WP') or lastWordTag.startswith('WP'):
        return True
    elif secondLastWordTag.startswith('WP') or secondLastWordTag.startswith('WP'):
        return True
    elif (firstWordTag.startswith('VBZ') or firstWordTag.startswith('VBP')) or firstWordTag.startswith('MD'):
        return True

    return False

def deviseCharacter(queries):
    # First query wikia to get possible matching articles
    articleIDs = queryWikiaSearch(queries)

    ## If the search result returned articleIDs matching the query then scan them
    ## and then refine the optimal result returned to appear more human
    if articleIDs:
        answer , images = queryWikiaArticles(articleIDs, queries, additionalSearchKeywords)

        # Refinement 1. Append the response to a random response prefix
        filler = RESPONSE_STARTERS[random.randint(0, len(RESPONSE_STARTERS) - 1)]
        if filler:
            if pos_tag(word_tokenize(answer))[0][1] == 'NNP' or word_tokenize(answer)[0] == 'I':
                first = answer[0]
            else:
                first = answer[0].lower()

            answer = "%s%s%s" % (filler, first, answer[1:])

        # Refinement 2. Remove Parentheses in answer
        tempAnswer = ''
        removeText = 0
        removeSpace = False
        for i in answer:
            if removeSpace:
                removeSpace = False
            elif i == '(':
                removeText = removeText + 1
            elif removeText == 0:
                tempAnswer += i
            elif i == ')':
                removeText = removeText - 1
                removeSpace = True

        answer = tempAnswer

        # print("Harry's Response: %s" % answer)


    return answer

def deviseAnswer(taggedInput):
    # Before querying the wiki -- perform spell check!
    for word in [word for word in taggedInput if
                 len(word[0]) > 3 and (word[1].startswith('N') or word[1].startswith('J') or word[1].startswith('V'))]:
        correctSpelling = spellCheck(word[0])
        if not correctSpelling == word[0]:
            return SPELLING_ERROR % (correctSpelling, word[0])

    # Default Answer
    answer = NO_INFORMATION_AVAILABLE

    result = parser.parse(taggedInput)
    print("Regexp Parser Result for input %s : " % taggedInput),
    print(result)

    # Determine the query to enter into the wikia search and add any additional
    # search terms now so that when article refinement is performed the most accurate reply is returned
    queries = []
    additionalSearchKeywords = []

    ## GENERAL STRATEGY:
    ## Look through tagged input then fetch whole sentence fragments through subtrees.
    ## 1. If starts with Auxillary Verb then take the first NP as the query
    ## and everything to the right becomes additional search keywords.
    ## 2. If starts with WH-NP then take rightmost NP and everything in between becomes
    ## additional search keywords
    ## 3. If ends with WH-NP then take first NP and everything in between becomes
    ## additional search keywords

    queryPhraseType = 3

    ## Helper POS Tag Information to define the question phrase type
    firstWordTag = taggedInput[0][1]
    lastToken = taggedInput[len(taggedInput) - 1][0]
    lastWordTag = taggedInput[len(taggedInput) - 1][1]
    secondLastWordTag = taggedInput[len(taggedInput) - 2][1]

    if firstWordTag.startswith('WP') or firstWordTag.startswith('WRB'):
        queryPhraseType = 2
    elif lastWordTag.startswith('WP') or lastWordTag.startswith('WP'):
        queryPhraseType = 3
    elif secondLastWordTag.startswith('WP') or secondLastWordTag.startswith('WP'):
        queryPhraseType = 3
    elif (firstWordTag.startswith('VBZ') or firstWordTag.startswith('VBP')) or firstWordTag.startswith('MD'):
        queryPhraseType = 1

    i = 0
    for subtree in result.subtrees():

        # Skip the first subtree (which is the entire tree)
        if i == 0:
            i = i + 1
            continue

        # Skip the first NP found if question starts with WH-NP or auxiliary VP
        if (queryPhraseType == 2 or queryPhraseType == 1) and i == 1:
            i = i + 1
            continue

        # Add NP to list of queries
        if subtree.label() == 'NP':
            queries.append(' '.join([(a[0]).encode('utf-8') for a in subtree.leaves()]))

        # Add VP and PPs to additional search keywords
        else:
            additionalSearchKeywords.append(' '.join([(a[0]).encode('utf-8') for a in subtree.leaves()]))

        i = i + 1

    ## Perform additional refinements to the list of queries and keywords

    # Refinement 1. If question phrase ends in WH-noun remove the last query
    if (queryPhraseType == 3 and len(queries) > 1) and (
        lastWordTag.startswith('W') or secondLastWordTag.startswith('W')):
        queries = queries[0:len(queries) - 1]

    # Refinement 2. Remove posseive affix from keywords if it exists
    additionalSearchKeywords = [keyword.replace("'s", "") for keyword in additionalSearchKeywords]

    # # Refinement 3. Replace 'you' and 'your' with 'Hermione Granger' in queries and keywords
    # addHarryQuery = False
    #
    # for query in queries:
    #     if 'your' in query or 'you' in query:
    #         addHarryQuery = True
    #
    # for keyword in additionalSearchKeywords:
    #     if 'your' in keyword or 'you' in keyword:
    #         addHarryQuery = True
    #
    # queries = [query.replace('your', '').replace('you', '') for query in queries]
    # additionalSearchKeywords = [keyword.replace('your', '').replace('you', '') for keyword in additionalSearchKeywords]

    # if addHarryQuery:
    #     queries.append('Harry Potter')

    # Refinement 4. Remove query terms from additionalSearchKeywords to avoid duplication
    for query in queries:
        additionalSearchKeywords = [keyword.replace(query, "") for keyword in additionalSearchKeywords]

    # Refinement 5. Remove empty strings from queries and additionalSearchKeywords
    additionalSearchKeywords = [value for value in additionalSearchKeywords if value != ' ' and value != '']
    queries = [value for value in queries if value != '']

    print("Wikia Queries : %s " % queries)
    print("Search Keywords : %s " % additionalSearchKeywords)

    ## If there are queries perform wikia search
    ## for articles and scan through article text for a relevant response
    if queries:

        # First query wikia to get possible matching articles
        articleIDs = queryWikiaSearch(queries)

        ## If the search result returned articleIDs matching the query then scan them
        ## and then refine the optimal result returned to appear more human
        if articleIDs:
            answer ,images = queryWikiaArticles(articleIDs, queries, additionalSearchKeywords)

            # Refinement 1. Append the response to a random response prefix
            filler = RESPONSE_STARTERS[random.randint(0, len(RESPONSE_STARTERS) - 1)]
            if filler:
                if pos_tag(word_tokenize(answer))[0][1] == 'NNP' or word_tokenize(answer)[0] == 'I':
                    first = answer[0]
                else:
                    first = answer[0].lower()

                answer = "%s%s%s" % (filler, first, answer[1:])

            # Refinement 2. Remove Parentheses in answer
            tempAnswer = ''
            removeText = 0
            removeSpace = False
            for i in answer:
                if removeSpace:
                    removeSpace = False
                elif i == '(':
                    removeText = removeText + 1
                elif removeText == 0:
                    tempAnswer += i
                elif i == ')':
                    removeText = removeText - 1
                    removeSpace = True

            answer = tempAnswer

    # print("Harry's Response: %s" % answer)
    return answer, images

def spellCheck(word):
    correctSpelling = correct(word.lower())
    if correctSpelling:
        return correctSpelling
    return

def words(text): return re.findall('[a-zA-Z]+', text)


def train(features):
    model = collections.defaultdict(lambda: 1)
    for f in features:
        model[f] += 1
    return model


NWORDS = train(words(file('hp-lexicon.txt').read()))

alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'


def edits1(word):
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = [a + b[1:] for a, b in splits if b]
    transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b) > 1]
    replaces = [a + c + b[1:] for a, b in splits for c in alphabet if b]
    inserts = [a + c + b for a, b in splits for c in alphabet]
    return set(deletes + transposes + replaces + inserts)


def known_edits2(word):
    return set(e2 for e1 in edits1(word) for e2 in edits1(e1) if e2 in NWORDS)


def known(words): return set(w.lower() for w in words if w in NWORDS)


def correct(word):
    candidates = known([word]) or known(edits1(word)) or known_edits2(word) or [word]
    return max(candidates, key=NWORDS.get)

def queryWikiaSearch(queries):
    articleIDs = []

    # Loop through all queries and find all matching articleIDs to search
    for query in queries:
        # Format Search Query URL
        SEARCH_QUERY_TEMPLATE['query'] = query
        searchUrl = WIKIA_API_URL
        searchUrl += SEARCH_URI
        searchUrl += urllib.urlencode(SEARCH_QUERY_TEMPLATE)

        # Open URL and fetch json response data
        try:
            results = urllib2.urlopen(searchUrl)
            resultData = json.load(results)
        except urllib2.HTTPError:
            continue

        # If there is a response then take the first result article
        # and return the url
        if resultData['total'] > 0:
            articleIDs.append([resultData['items'][0]['id'], query])

    return articleIDs

def queryWikiaArticles(articleIDs, queries, searchRefinement):
    answer = ''
    answerScore = 0
    images = []

    for articleID in articleIDs:
        print 'Article ID: '+ str(articleID[0])
        # Format Article URL
        ARTICLE_QUERY_TEMPLATE['id'] = articleID[0]
        articleUrl = WIKIA_API_URL
        articleUrl += ARTICLES_URI
        articleUrl += urllib.urlencode(ARTICLE_QUERY_TEMPLATE)

        # Open URL and fetch json response text
        results = urllib2.urlopen(articleUrl)
        resultData = json.load(results)

        # Select the top scoring sentences from the article and compare with pre-existing top answer
        answerWithScore, images = refineWikiaArticleContent(articleID[1], resultData, queries, searchRefinement)

        if answerWithScore[1] > answerScore:
            answerScore = answerWithScore[1]
            answer = answerWithScore[0]

            # If response has to do with Hermione replace 3rd person pronouns with 1st person pronouns
            # for query in queries:
            #     if 'Harry' in query.rsplit(" "):
            #         answer = answer.replace('He', 'I').replace('his', 'my')

            # Replace any keyword hinting at Hermione with the proper personal pronoun and if followed by 'is' replace with 'am'
            # answer = answer.replace('Harry\'s', 'my').replace('Harry Potter is', 'I am').replace('Harry is', 'I am').replace(
            #     'Harry James Potter', 'I').replace('Harry Potter', 'I').replace('Harry', 'I')

        # If there is no answer then take the first two sentences from the article as a relevant answer
        if not answer:
            try:
                print 'No Answer'
                sentences = sent_tokenize(resultData['sections'][0]['content'][0]['text'].replace('b.', 'born'))
                # Replace any keyword hinting at Hermione with the proper personal pronoun and if followed by 'is' replace with 'am'
                # answer = ' '.join(sentences[0:2]).replace('Harry\'s', 'my').replace('Harry Potter is', 'I am').replace('Harry is', 'I am').replace(
                #     'Harry James Potter', 'I').replace('Harry Potter', 'I').replace('Harry', 'I')
                answer = ' '.join(sentences[0:2])

            except IndexError:
                continue

    return answer,images


def refineWikiaArticleContent(specificQuery, articleData, queries, searchRefinement):
    ## top two sentences
    firstSentenceScore = 0
    secondSentenceScore = 0
    firstSentence = ''
    secondSentence = ''
    images = []

    ## loop through sections
    for section in articleData['sections']:
        ## loop through images
        for image in section['images']:
            if not 'src' in image:
                continue
            print image['src']
            for query in queries:
                if 'caption' in image:
                    if query in image['caption']:
                        src = image['src'].split("/revision/")[0]
                        image_element ={
                            "title": image['caption'],
                            "image_url": url_for('static', filename='"'+ src +'"', _external=True)
                        }
                        images.append(image_element)
                        break

        ## loop through content
        for content in section['content']:
            ## fetch text and loop through sentences
            if not 'text' in content:
                continue

            for sentence in sent_tokenize(content['text'].replace('b.', 'born')):
                sentenceScore = 0

                ## loop through refinements to see if they're in the sentence
                for refinement in searchRefinement:

                    if refinement in sentence:
                        sentenceScore = sentenceScore + 0.5 + (sentence.count(refinement) / len(sentence.rsplit(" ")))

                    for query in queries:

                        if ' '.join([query, refinement]) in sentence:
                            sentenceScore = sentenceScore + 0.25
                        if ' '.join([refinement, query]) in sentence:
                            sentenceScore = sentenceScore + 0.25

                ## loop through queries to see if they're in the sentence
                for query in queries:

                    if query in sentence:
                        sentenceScore = sentenceScore + 1 + sentence.count(query) / len(sentence.rsplit(" "))
                        if not query == specificQuery:
                            sentenceScore = sentenceScore + 0.5

                    for word in query.split(" "):
                        if word in sentence:
                            sentenceScore = sentenceScore + 1 / len(queries)

                ## If score in top two re-adjust scores and sentences
                if sentenceScore > secondSentenceScore:
                    if sentenceScore > firstSentenceScore:
                        secondSentence = firstSentence
                        secondSentenceScore = firstSentenceScore
                        firstSentence = sentence
                        firstSentenceScore = sentenceScore
                    else:
                        secondSentence = sentence
                        secondSentenceScore = sentenceScore

    # If an answer was found determine an appropriate response length and return the answer and score
    if firstSentence:
        if len(firstSentence) + len(secondSentence) > 1000 or secondSentenceScore < firstSentenceScore:
            secondSentence = ''
            secondSentenceScore == 0
        return [' '.join([firstSentence, secondSentence]), firstSentenceScore + secondSentenceScore],images
    else:
        return ['', 0],images

def handle_help(user_id):
    intro = "I can help you know more about the Harry Potter World ,Characters ,Spells and much more!!"
    FB.send_message(os.environ["PAGE_ACCESS_TOKEN"], user_id, intro)
    FB.send_intro_screenshots(app, os.environ["PAGE_ACCESS_TOKEN"], user_id)

def handle_characters(user_id):
    intro = "You can ask me about any character simply by asking me :D !!\nJust like that \"Who's Harry Potter?\"\n\"Who's pet was Fang?\""
    FB.send_message(os.environ["PAGE_ACCESS_TOKEN"], user_id, intro)
    # FB.send_intro_screenshots(app, os.environ["PAGE_ACCESS_TOKEN"], user_id)

def handle_spells(user_id):
    intro = "You can ask me about any spell simply by asking me :D !!\nJust like that \"What is Wingardium Leviosa?\"\n\"What is Expecto Patronum?\""
    FB.send_message(os.environ["PAGE_ACCESS_TOKEN"], user_id, intro)
    # FB.send_intro_screenshots(app, os.environ["PAGE_ACCESS_TOKEN"], user_id)


def handle_first_time_user(sender_id,user):
    user_id = sender_id
    token = os.environ["PAGE_ACCESS_TOKEN"]

    # hi = "%s Wizard, Nice to meet you :)" % (NLP.sayHiTimeZone(user))
    hi = "%s %s, nice to meet you" % (NLP.sayHiTimeZone(user), user['first_name'])
    FB.send_message(token, user_id, hi)

    FB.send_picture(token, user_id, 'https://media.giphy.com/media/12kmDEDUpTWe3e/giphy.gif')

    handle_help(user_id)
    FB.send_message(token, user_id, "Next time just tell me \"Help\" to view this again :D")


def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(message):  # simple wrapper for logging to stdout on heroku
    # print str(message)
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)