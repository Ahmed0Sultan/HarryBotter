import time, string, random, re
from bad_words import BAD_WORDS
import FacebookAPI as FB
from datetime import datetime, timedelta
from pattern.en import parsetree, singularize
from pattern.search import search

# Random response sets
no_response = ["*scratch my head* :(", "How do I respond to that... :O", "I don't know you can ask Hermione... :/", "I can be not-so-smart from time to time... :(", "Err... you know I'm not the real Harry Potter, right? :O"]
error = ["Sorry I've got a little bit sick. BRB in 2 min :(", "Oops... 404 My Witty Mind Not Found :O", "Oops... My brain went MIA in the cloud, BRB in 2 :(", "Hmm... How should I respond to that... :O"]
looking_replies = ["Sure, give me a few seconds... B-)", "Scanning the world... :D", "Zoom zoom zoom..."]
thanks_replies = ["You are welcome ;)","Not at all","Don't mention it :D","No problem :D"," :D ","My pleasure ;)"]
# END random response sets



def removePunctuation(inp_str):
    return inp_str.translate(None, string.punctuation)

def isAskingBotInformation(sentence):
    m = search('what *+ your name', sentence)
    if len(m) > 0:
        return True

    m = search('VP+ *+ your name', sentence)
    if len(m) > 0:
        return True

    m = search('who *+ your creator|dad|mom|father|mother|papa|mama|daddy|mommy', sentence)
    if len(m) > 0:
        return True

    m = search('VP+ *+ your creator|dad|mom|father|mother', sentence)
    if len(m) > 0:
        return True

    m = search('who made|are|created|create|wrote|gave_birth|built you', sentence)
    if len(m) > 0:
        return True

    return False
def isEasterEggs(sentence):
    m = re.search('(love|like|lov|luv) (you|u)', sentence, re.I)
    if m:
        return True

    m = re.search('do you (love|like) me', sentence, re.I)
    if m:
        return True

    m = re.search('do you hate me', sentence, re.I)
    if m:
        return True

    m = re.search('hate (you|u)', sentence, re.I)
    if m:
        return True

    m = re.search('suck', sentence, re.I)
    if m:
        return True
    return False

def isGreetings(inp_str):
    string = inp_str.lower().split(" ")
    if len(string) > 3:
        return False
    greetings = ['hi','hey','hello', 'hola','greetings', 'good morning','morning', 'good afternoon','afternoon', 'good evening']
    for word in greetings:
        if word in string[:3]:
            return True
    return False

def isThanking(inp_str):
    string = inp_str.lower().split(" ")
    thanks = ['thanks', 'thank','good','great','awesome','fantastic','terrific','fabulous','nice']
    for word in thanks:
        if word in string:
            return True
    return False

def isEmoji(inp_str):
    # inp = inp_str.encode('raw_unicode_escape','ignore')
    # if inp[0:2] == '\U' or '\u':
    #     return True
    m = re.match('(:.)+',inp_str)
    if m:
        return True
    m = re.match('(.-.)+', inp_str)
    if m:
        return True
    m = re.match('(._.)+', inp_str)
    if m:
        return True
    return False

def handleEmoji(inp_str):
    inp = inp_str.encode('raw_unicode_escape', 'ignore')
    if inp[0:2] == '\U' or '\u':
        return inp_str
    m = re.match('(:.)+', inp_str)
    if m:
        return inp_str.capitalize()
    return inp_str


def isGoodbye(inp_str):
    string = inp_str.lower().split(" ")
    byes = ['bye', 'see you','goodbye','bye bye','miss you']

    for word in byes:
        if word in string:
            return True
        elif word == inp_str.lower():
            return True
    return False

def isMemoCommandOnly(inp_str):
    s = inp_str.lower().split(" ")
    if s[0] in ['memorize','memorized'] and len(s) < 6:
        return True
    regEx = "(memorize)( this)?([\w\d ]{0,15}(?<!except)for me)?"
    command = re.search(regEx, inp_str)
    if command != None:
        remaining = inp_str.replace(command.group(0), "").strip()
        if remaining == "":
            return True
    return False

def isMemo(inp_str):
    regEx = "memorize( this)?([\w\d ]{0,15}(?<!except)for me)?"
    command = re.search(regEx, inp_str.lower())
    if command != None:
        return True
    return False

def get_memo_content(inp_str):
    regEx = "memorize( this)?([\w\d ]{0,15}(?<!except)for me)?"
    command = re.search(regEx, inp_str.lower())
    if command == None:
        return inp_str
    return inp_str.replace(command.group(0), "").strip() # strip trailing space

# input: g.user, i.e. mongodb user object
def sayHiTimeZone(user):
    user_now = getUserTime(user)
    if user_now.hour > 5 and user_now.hour <= 12:
        return oneOf(["Good morning","Shiny day isn't it", "What a morning", "Morningggg"])
    elif user_now.hour > 12 and user_now.hour < 19:
        return oneOf(["Good afternoon","How's your afternoon", "Afternoooooon", "What a day"])
    else:
        return oneOf(["Good evening","Good evening", "What's rolling for dinner"])

# input: g.user
def sayByeTimeZone(user):
    user_now = getUserTime(user)
    goodnights = ["Good night", "Have a good night", "Bye now", "See you later"]
    byes = ["Goodbye", "Bye then", "See you later", "Bye, have a good day"]
    
    if user_now.hour > 20:
        return "%s :)"%oneOf(goodnights)
    else:
        return "%s :)"%oneOf(byes)

# input: g.user
def recentChat(user):
    last_seen = user['last_seen'] 
    timestamp = datetime.strptime(last_seen,"%Y-%m-%d %H:%M:%S")
    time_since_chat = datetime.now() - timestamp
    recent60min = timedelta(minutes=60)
    if time_since_chat < recent60min:
        return True
    else:
        return False

# input: g.user
def getUserTime(user):
    user_tz = user['timezone']
    offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
    server_tz = offset / 60 / 60 * -1
    time_diff = user_tz - server_tz
    server_now = datetime.now()
    return server_now + timedelta(hours=time_diff)

# input: pattern.en sentence object
def findVerb(sentence):
    result = []
    for chunk in sentence.chunks:
        if chunk.type in ['VP']:
            strings = [w.string for w in chunk.words if w.type in ['VB','VBP']]
            result.extend(strings)
    return result

# input: pattern.en sentence object
def findNounPhrase(sentence):
    res = ""
    for chunk in sentence.chunks:
        if chunk.type == 'NP':
            res += " ".join([w.string for w in chunk.words if w.type not in ['PRP', 'DT']])
            res += " "
    for verb in ['find','get','show','search']:
        res = res.replace(verb, "")
    return res

# input: pattern.en sentence object
def findProperNoun(sentence):
    for chunk in sentence.chunks:
        if chunk.type == 'NP':
            for w in chunk.words:
                if w.type == 'NNP':
                    return w.string
    return None

# input: pattern.en sentence object
def isYelp(sentence):
    verbs = findVerb(sentence)
    noun_phrases = findNounPhrase(sentence)
    # If match key verbs
    yelpVerbs = ['eat', 'drink', 'find', 'display', 'get']
    for verb in verbs:
        if verb.lower() in yelpVerbs:
            if "news" in noun_phrases or "information" in noun_phrases and "news stand" not in noun_phrases and "newsstand" not in noun_phrases:
                return False

            yelpNouns = ['restaurant', 'food', 'drink', 'shop', 'store', 'bar', 'pub']
            for noun in yelpNouns:
                if noun in noun_phrases:
                    return True

    # If match question/command structure
    # "is there" + noun phrase 
    if "is there" in sentence.string \
        or "are there" in sentence.string \
        and noun_phrases != "":

        return True
    
    # noun phrase + "near by"
    nearby = nearBy(sentence)
    if noun_phrases != "" and nearby:
        return True

    m = search('{fine|find|get|find|show|search} { *+ }', sentence)
    # Sometimes Speech to Text misunderstood "find" as "fine"
    print m
    if len(m) > 0:
        return True

    return False

# input: string
def isDismissPreviousRequest(string):
    string = string.lower()
    stop_signals = ["never mind", "stop", "dismiss", "cancel", "dont want", "dont need", "do not"]
    if "no" in string:
        return True
    for signal in stop_signals:
        if signal in string:
            return True
    return False

# input: pattern.en sentence object
def nearBy(sentence):
    res = ""
    for chunk in sentence.chunks:
        if chunk.type in ['PP', 'ADVP']:
            res += " ".join([w.string for w in chunk.words if w.type in ['RB', 'PRP', 'IN']])
            res += " "
    res = res.strip()
    if res in ['near me', 'around here', 'around', 'near here', 'nearby', 'near by', 'close by', 'close']:
        return True
    return False

# input: pattern.en sentence object
def fullQuery(sentence):
    new_str = ""
    for word in sentence.words:
        if word.string in ['places', 'locations', 'spots']:
            continue
        new_word = singularize(word.string) if word.type == "NNS" else word.string
        new_str += new_word + " "
    singularized_sentence = parsetree(new_str, relations=True, lemmata=True)

    
    m = search('{JJ? NN+} IN {JJ? NN+}', singularized_sentence)
    query = {}
    if len(m) > 0:
        query["term"] = m[0].group(1).string
        query["location"] = m[0].group(2).string
    return query


def oneOf(arr):
    rand_idx = random.randint(0,len(arr) - 1)
    return arr[rand_idx]

def randOneIn(chance):
    i = random.randint(1,chance)
    if i == chance:
        return True
    return False

def badWords(string):
    for word in string.split(" "):
        if word.lower() in BAD_WORDS:
            return True
    return False

def openNow(sentence):
    if "open now" in sentence.string.lower() or "opens now" in sentence.string.lower():
        return True
    return False

def hasWifi(sentence):
    string = removePunctuation(sentence.string.lower())
    if "wifi" in string:
        return True
    return False

def isGetNews(sentence):
    m = search('{VP} {VBG+? JJ+?} {news | information} about|on|regarding { *+ }', sentence)
    if len(m) > 0:
        if m[0].group(1).string.lower() in ['look', 'get', 'find', 'tell', 'show', 'fetch', 'search']:
            return True

    # Solve special case when "Get" at the beginning of sentence is recognized as 
    # a proper noun
    m = search('get|find|look *+ news|information about|on|regarding', sentence)
    if len(m) > 0:
        return True

    return False

def getNewsQuery(sentence):
    m = search('{NP+} about|on|regarding { *+ }', sentence)
    if len(m) > 0:
        return m[0].group(2).string.replace('.','')
def answerWithOkay(sentence):
    reply = 'Okay'

    m = search('Yes|yes|No|no|Okay|okay|Ok|ok',sentence)
    if len(m) > 0:
        return True

    m = re.search(".* shut .* up .*", sentence,re.I)
    if m:
        return True
    return False

def isFunny(sentence):
    reply_funny = ['Glad you like it :D',':D :D']

    m = re.search('\b(h|H)+\b',sentence,re.I)
    if m:
        return True

    m = re.search('\b((h|H)a)+\b', sentence,re.I)
    if m:
        return True

    m = re.search('\b((h|H)a+)+\b', sentence,re.I)
    if m:
        return True

    m = re.search('.* (f|F)unny', sentence,re.I)
    if m:
        return True
    m = re.search('wow', sentence, re.I)
    if m:
        return True
    m = re.search('(I|i) .+ like .*', sentence,re.I)
    if m:
        return True
    return False

def handleEasterEggs(sentence):
    love_responses = ['No, I love you <3','Hearing you say that makes me so happy <3','It means so much that you\'re opening up to me like this. Thank you <3','I\'m so happy you told me <3']
    hate_responses = ['Well, I like you! :/','Thank you :)',':) :)','Yet you are still here']

    m = re.search('(love|like|lov|luv) (you|u)', sentence, re.I)
    if m:
        return oneOf(love_responses)

    m = re.search('do you (love|like) me', sentence, re.I)
    if m:
        return 'Of course I love you <3'

    m = re.search('do you hate me', sentence, re.I)
    if m:
        return 'Of course not, I love you <3'

    m = re.search('hate (you|u)', sentence, re.I)
    if m:
        return oneOf(hate_responses)

    m = re.search('suck', sentence, re.I)
    if m:
        return oneOf(hate_responses)
    return False

def handleBotInfo(sentence):
    name = ["Botter ... Harry Botter B-)", "The most powerful Wizard-Bot! ;)", "You knew already *tsk tsk*"]
    creator = ["It's a mystery :O", "It remains a mystery to me even :(", "It was erased from my memory from the start :("]

    m = search('what *+ your name', sentence)
    if len(m) > 0:
        return oneOf(name)

    m = search('VP+ *+ your name', sentence)
    if len(m) > 0:
        return oneOf(name)

    m = search('who *+ your creator|dad|mom|father|mother|papa|mama|daddy|mommy', sentence)
    if len(m) > 0:
        return oneOf(creator)

    m = search('VP+ *+ your creator|dad|mom|father|mother|papa|mama|daddy|mommy', sentence)
    if len(m) > 0:
        return oneOf(creator)

    m = search('who made|created|create|wrote|gave_birth|built you', sentence)
    if len(m) > 0:
        return oneOf(creator)

    m = search('who made|created|create|wrote|gave_birth|built you for real', sentence)
    if len(m) > 0:
        return "You are among the few who I tell: All I know about my creator is the initials AS :D"
    m = search('who are you', sentence)
    if len(m) > 0:
        return oneOf(name)

    return "Can you guess? ;)"