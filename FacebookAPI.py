import requests, json
from flask import url_for

def get_user_fb(token, user_id):
    r = requests.get("https://graph.facebook.com/v2.6/" + user_id,
                    params={"fields": "first_name,last_name,profile_pic,locale,timezone,gender"
                        ,"access_token": token
                    })
    if r.status_code != requests.codes.ok:
        print r.text
        return
    user = json.loads(r.content)
    return user

def show_typing(token, user_id, action='typing_on'):
  r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=json.dumps({
                          "recipient": {"id": user_id},
                          "sender_action": action
                      }),
                      headers={'Content-type': 'application/json'})
  if r.status_code != requests.codes.ok:
        print r.text

def send_message(token, user_id, text):
    """Send the message text to recipient with id recipient.
    """
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=json.dumps({
                          "recipient": {"id": user_id},
                          "message": {"text": text.decode('unicode_escape')}
                      }),
                      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print r.text

def send_emoji(token, user_id, text):
    """Send the message text to recipient with id recipient.
    """
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=json.dumps({
                          "recipient": {"id": user_id},
                          "message": {"text": text}
                      }),
                      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print r.text


def send_picture(token, user_id, imageUrl, title="", subtitle=""):
    if title != "":
        data = {"recipient": {"id": user_id},
                  "message":{
                      "attachment": {
                          "type": "template",
                          "payload": {
                              "template_type": "generic",
                              "elements": [{
                                  "title": title,
                                  "subtitle": subtitle,
                                  "image_url": imageUrl
                              }]
                          }
                      }
                    }
              }
    else:
        data = { "recipient": {"id": user_id},
                "message":{
                  "attachment": {
                      "type": "image",
                      "payload": {
                          "url": imageUrl
                      }
                  }
                }
            }
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=json.dumps(data),
                      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print r.text    

def send_quick_replies_yelp_search(token, user_id):
    # options = [Object {name:value, url:value}, Object {name:value, url:value}]
    quickRepliesOptions = [
        {"content_type":"text",
         "title": "Get more suggestions",
         "payload": 'yelp-more-yes'
        },
        {"content_type":"text",
         "title": "That's good for me",
         "payload": 'yelp-more-no'
        }
    ]
    data = json.dumps({
            "recipient":{ "id": user_id },
            "message":{
                "text":"Do you want to find more results? :D",
                "quick_replies": quickRepliesOptions
                }
            })
    data = data.encode('utf-8')
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
        params={"access_token": token},
        data=data,
        headers={'Content-type':'application/json'})

    if r.status_code != requests.codes.ok:
        print r.text

def send_quick_replies_yelp_save_location(token, user_id, location=None):
    # options = [Object {name:value, url:value}, Object {name:value, url:value}]
    quickRepliesOptions = [
        {"content_type":"text",
         "title": "Sure",
         "payload": 'yelp-save-location-yes'
        }]
    if location != None: # Place this here to make sure this option comes second
        rename = {"content_type":"text",
         "title": "I'll rename it",
         "payload": 'yelp-save-location-rename'
        }
        quickRepliesOptions.append(rename)
    no = {"content_type":"text",
         "title": "No, thank you",
         "payload": 'yelp-save-location-no'
        }
    quickRepliesOptions.append(no)
    
    if location == None:
        message = "Do you want me to save this location?"
    else:
        message = "Do you want me to save this location as \"%s\" for the future? :D"%(location)
    data = json.dumps({
            "recipient":{ "id": user_id },
            "message":{
                "text": message,
                "quick_replies": quickRepliesOptions
                }
            })
    data = data.encode('utf-8')
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
        params={"access_token": token},
        data=data,
        headers={'Content-type':'application/json'})

    if r.status_code != requests.codes.ok:
        print r.text

def send_quick_replies_yelp_suggest_location(token, user_id, locations):
    quickRepliesOptions = []
    i = 0
    for location in locations:
        location_name = location['name'][:17] + "..." if len(location['name']) > 20 else location['name']

        obj = {"content_type":"text",
         "title": location_name,
         "payload": 'yelp-cached-location-%s'%(i)
        }
        quickRepliesOptions.append(obj)
        i += 1
    
    data = json.dumps({
            "recipient":{ "id": user_id },
            "message":{
                "text":"Or choose one of the saved locations :D",
                "quick_replies": quickRepliesOptions
                }
            })
    data = data.encode('utf-8')
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
        params={"access_token": token},
        data=data,
        headers={'Content-type':'application/json'})

    if r.status_code != requests.codes.ok:
        print r.text

def send_yelp_results(token, user_id, businesses):
    options = []

    for business in businesses:
        subtitle = ""
        if 'price' in business and business['price'] != "":
            subtitle += business['price'] + " - "
        subtitle += business['address'] 
        if 'distance' in business:
            subtitle += " (" + str(business['distance']) + " mi.)"
        if 'is_open_now' in business:
            subtitle += "\n" + "Open now - " if business['is_open_now'] else "\n" 
        if 'hours_today' in business and len(business['hours_today']) > 0:
            subtitle += "Hours today: %s"%(business['hours_today'])
        subtitle += "\n" + business['categories']

        img_url = business['image_url'] if business['image_url'] != "" else url_for('static', filename='assets/img/empty-placeholder.jpg', _external=True)
        
        obj = {
                "title": business['name'] + " - " + business['rating'] ,
                "image_url": img_url,
                "subtitle": subtitle,
                "buttons":[
                    {
                    "type":"web_url",
                    "url": business['url'],
                    "title":"View details"
                    }
                    # ,{
                    # "type":"postback",
                    # "title":"Start Chatting",
                    # "payload":"USER_DEFINED_PAYLOAD"
                    # }          
                ]
                }
        options.append(obj) 
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=json.dumps({
                            "recipient": {"id": user_id},
                            "message":{
                                "attachment":{
                                    "type":"template",
                                    "payload":{
                                        "template_type":"generic",
                                        "elements": options
                                    }
                                }
                            }
                      }),
                      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print r.text

def send_url(token, user_id, text, title, url):
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=json.dumps({
                            "recipient": {"id": user_id},
                            "message":{
                                "attachment":{
                                    "type":"template",
                                    "payload":{
                                        "template_type":"button",
                                        "text": text,
                                        "buttons":[
                                            {
                                            "type":"web_url",
                                            "url": url,
                                            "title": title
                                            }
                                        ]
                                    }
                                }
                            }
                      }),
                      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print r.text


def send_quick_replies_characters(token, user_id,intro):
    quickRepliesOptions = [
        {"content_type": "text",
         "title": "Harry Potter",
         "payload": 'character-harry-potter'
         },
        {"content_type": "text",
         "title": "Ron Weasley",
         "payload": 'character-ron-weasley'
         },
         {"content_type": "text",
         "title": "Hermione Granger",
         "payload": 'character-hermione-granger'
         },
        {"content_type": "text",
         "title": "Albus Dumbledore",
         "payload": 'character-albus-dumbledore'
         }
    ]
    data = json.dumps({
        "recipient": {"id": user_id},
        "message": {
            "text": intro,
            "quick_replies": quickRepliesOptions
        }
    })
    data = data.encode('utf-8')
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=data,
                      headers={'Content-type': 'application/json'})

    if r.status_code != requests.codes.ok:
        print r.text

def send_quick_replies_spells(token, user_id,intro):
    quickRepliesOptions = [
        {"content_type": "text",
         "title": "Aguamenti",
         "payload": 'spell-aguamenti'
         },
        {"content_type": "text",
         "title": "Expecto Patronum",
         "payload": 'spell-expecto-patronum'
         },
         {"content_type": "text",
         "title": "Avada Kedavra",
         "payload": 'spell-avada-kedavra'
         },
        {"content_type": "text",
         "title": "Alohomora",
         "payload": 'spell-alohomora'
         }
    ]
    data = json.dumps({
        "recipient": {"id": user_id},
        "message": {
            "text": intro,
            "quick_replies": quickRepliesOptions
        }
    })
    data = data.encode('utf-8')
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=data,
                      headers={'Content-type': 'application/json'})

    if r.status_code != requests.codes.ok:
        print r.text

def send_quick_replies_places(token, user_id,intro):
    quickRepliesOptions = [
        {"content_type": "text",
         "title": "Diagon Alley",
         "payload": 'place-diagon-alley'
         },
        {"content_type": "text",
         "title": "Godric's Hollow",
         "payload": 'place-godric-hollow'
         },
         {"content_type": "text",
         "title": "Hogsmeade",
         "payload": 'place-hogsmeade'
         },
        {"content_type": "text",
         "title": "Hogwarts Express",
         "payload": 'place-hogwarts-express'
         }
    ]
    data = json.dumps({
        "recipient": {"id": user_id},
        "message": {
            "text": intro,
            "quick_replies": quickRepliesOptions
        }
    })
    data = data.encode('utf-8')
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=data,
                      headers={'Content-type': 'application/json'})

    if r.status_code != requests.codes.ok:
        print r.text

def send_quick_replies_help(token, user_id,intro):
    quickRepliesOptions = [
        {"content_type": "text",
         "title": "Characters",
         "payload": 'Harry_Botter_Characters'
         },
        {"content_type": "text",
         "title": "Spells",
         "payload": 'Harry_Botter_Spells'
         },
         {"content_type": "text",
         "title": "Places",
         "payload": 'Harry_Botter_Places'
         },
         {"content_type": "text",
         "title": "Get Points",
         "payload": 'Harry_Botter_Get_Points'
         }
    ]
    data = json.dumps({
        "recipient": {"id": user_id},
        "message": {
            "text": intro,
            "quick_replies": quickRepliesOptions
        }
    })
    data = data.encode('utf-8')
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=data,
                      headers={'Content-type': 'application/json'})

    if r.status_code != requests.codes.ok:
        print r.text

def send_group_pictures(app, token, user_id,images):

    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
          params={"access_token": token},
          data=json.dumps({
                "recipient": {"id": user_id},
                "message":{
                    "attachment":{
                        "type":"template",
                        "payload":{
                            "template_type":"generic",
                            "elements": images
                        }
                    }
                }
          }),
          headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print r.text

def send_intro_screenshots(app, token, user_id):
    chat_speak = {
        "title": 'You can chat with me and ask me anything about Harry Potter world',
        "image_url": url_for('static', filename="assets/img/chat.jpg", _external=True),
        "subtitle": 'I understand natural language (I try to be smarter everyday :D)'
    }
    characters = {
        "title": "Get to know characters better",
        "image_url": url_for('static', filename="assets/img/hpcast1.jpg", _external=True),
        "subtitle": "Type \"Characters\" or choose from menu"
    }
    spells = {
        "title": "Get to know spells and how they work",
        "image_url": url_for('static', filename="assets/img/harrypotterspells.jpg", _external=True),
        "subtitle": "Type \"Spells\" or choose from menu",
    }
    places = {
        "title": "Get to know more places in the magic world",
        "image_url": url_for('static', filename="assets/img/places.jpg", _external=True),
        "subtitle": "Type \"Places\" or choose from menu"
    }
    compete = {
        "title": "Compete with friends to win the House Cup",
        "image_url": url_for('static', filename="assets/img/cup.jpg", _external=True),
        "subtitle": "Choose Great Hall from menu and begin your journey"
    }


    options = [chat_speak, characters, spells, places,compete]

    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
          params={"access_token": token},
          data=json.dumps({
                "recipient": {"id": user_id},
                "message":{
                    "attachment":{
                        "type":"template",
                        "payload":{
                            "template_type":"generic",
                            "elements": options
                        }
                    }
                }
          }),
          headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print r.text

def send_trending_news(token, user_id, posts):
    options = []
    for post in posts:
        img_url = post['image_url'] if post['image_url'] != "" else url_for('static', filename='assets/img/empty-placeholder.jpg', _external=True)
        obj = {
            "title": post['title'],
            "image_url": img_url,
            "subtitle": post['subtitle'],
            "buttons":[
                {
                "type":"web_url",
                "url": post['url'],
                "title":"Read more"
                }
            ]
        }
        options.append(obj) 
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=json.dumps({
                            "recipient": {"id": user_id},
                            "message":{
                                "attachment":{
                                    "type":"template",
                                    "payload":{
                                        "template_type":"generic",
                                        "elements": options
                                    }
                                }
                            }
                      }),
                      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print r.text


def set_menu():
    r = requests.post("https://graph.facebook.com/v2.6/me/thread_settings",
                    params={"access_token": 'EAAEPOb8cxn0BAIy98wL67t09MPbt3ZCCbdLhujNfmSSSgRThkNFa4Ts2Gfc36DpWs2m7Pbp3ZAhAypkST9O2ksxRZBiGYxiW1JZA5XvyFm5VD2mtlX2KtBNXquka1rNxACZBgaSfPso1HTiewJT3zAnDiNpPxRJZASbBJn6jglYgZDZD'},
                    data=json.dumps({
                        "setting_type" : "call_to_actions",
                        "thread_state" : "existing_thread",
                        "call_to_actions":[
                            {
                                "type": "postback",
                                "title": "View House",
                                "payload": "Harry_Botter_House"
                            },
                            {
                                "type": "nested",
                                "title": "Wiki",
                                "call_to_actions":[
                                    {
                                        "type": "postback",
                                        "title": "Characters",
                                        "payload": "Harry_Botter_Characters"
                                    },
                                    {
                                        "type": "postback",
                                        "title": "Spells",
                                        "payload": "Harry_Botter_Spells"
                                    },
                                    {
                                        "type": "postback",
                                        "title": "Places",
                                        "payload": "Harry_Botter_Places"
                                    }
                                ]
                            },
                            {
                                "type": "postback",
                                "title": "Help",
                                "payload": "Harry_Botter_Help"
                            },
                        ]
                    }),
                    headers={'Content-type': 'application/json'})
    print r.content
    if r.status_code != requests.codes.ok:
        print r.text

def set_get_started_button():

    r = requests.post("https://graph.facebook.com/v2.6/me/thread_settings",
                    params={"access_token": 'EAADhYj0lr14BAGP2HCx2mcYcxQbtQG7iXfaGpOieFsGlgJEYv0Y74bdIYtQ3UcnK1kktfUCDInciDniwTOm1c6l2Fq2GEBsm0Lu4syz5HUc41MGepASZBuXw1caZBkZBGRX5kIZCT7q5QOkiPVnZC3n8iBcqVMCBGnZCiSgscQogZDZD'},
                    data=json.dumps({
                        "setting_type":"call_to_actions",
                        "thread_state":"new_thread",
                        "call_to_actions":[
                            {
                            "payload":"OPTIMIST_GET_STARTED"
                            }
                        ]
                    }),
                    headers={'Content-type': 'application/json'})
    print r.content
    if r.status_code != requests.codes.ok:
        print r.text

# set_menu()
# set_get_started_button()