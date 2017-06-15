# coding=utf-8
import os
import sys, traceback
reload(sys)
sys.setdefaultencoding('utf-8')
import json
import dbAPI
import FacebookAPI as FB, NLP
from datetime import datetime

## Resources for querying API and parsing results
import re, collections, json, urllib, urllib2, random

from nltk import RegexpParser
from nltk.data import load
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize, sent_tokenize

import requests
from flask import Flask, request, render_template,url_for
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand

app = Flask(__name__)
token = os.environ["PAGE_ACCESS_TOKEN"]
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

WIKIA_API_URL = 'http://www.harrypotter.wikia.com/api/v1'
SEARCH_URI = '/Search/List/?'
ARTICLES_URI = '/Articles/AsSimpleJson?'
QUERY_RESULT_LIMIT = 25
SEARCH_QUERY_TEMPLATE = {'query': '', 'limit': QUERY_RESULT_LIMIT}
ARTICLE_QUERY_TEMPLATE = {'id': ''}

QBank = [
{'What is the spell that Harry used to defeat Voldemort in their final encounter?': [{'Expelliarmus':'CorrectAns'},{'Accio':'WrongAns'},{'Crucio':'WrongAns'},{'Diffindo':'WrongAns'}]},
{'Which of these spells is not an unforgivable curse?':[{'Lumos':'CorrectAns'},{'Imperio':'WrongAns'},{'Crucio':'WrongAns'},{'Avada Kedavra':'WrongAns'}]},
{'What is the punishment for using an unforgivable curse?':[{'A life sentence in Askaban':'CorrectAns'},{'Detention':'WrongAns'},{'No punishment':'WrongAns'},{'Execution':'WrongAns'}]},
{'What is the spell that unlocks a locked door?':[{'Levicorpus':'WrongAns'},{'Expulso':'WrongAns'},{'Alohamora':'CorrectAns'},{'Incendio':'WrongAns'}]},
{'What is the spell that Hermione uses to fix Harry\'s glasses in the first novel?':[{'Reparo':'CorrectAns'},{'Sectumsempra':'WrongAns'},{'Reducto':'WrongAns'},{'Stupefy':'WrongAns'}]},
{'What is the effect of the Stupefy spell?':[{'Explosion':'WrongAns'},{'Stinging':'WrongAns'},{'Stunning':'CorrectAns'},{'Transfiguration':'WrongAns'}]},
{'Which spell does Remus Lupin teach the class to fight off a Boggart?':[{'Riddikulus':'CorrectAns'},{'Scourgify':'WrongAns'},{'Sonorus':'WrongAns'},{'Imperio':'WrongAns'}]},
{'What is the spell that Harry learns from Snape\'s old Potions textbook?':[{'Portus':'WrongAns'},{'Alakazam':'WrongAns'},{'Sectumsempra':'CorrectAns'},{'Periculum':'WrongAns'}]},
{'Which spell is effective when fighting off Dementors?':[{'Expecto Patronum':'CorrectAns'},{'Erecto':'WrongAns'},{'Dissendium':'WrongAns'},{'Confundo':'WrongAns'}]},
{'Which spell causes the victim to become confused and befuddled?':[{'Muffliato':'WrongAns'},{'Lumos':'WrongAns'},{'Ferula':'WrongAns'},{'Confundo':'CorrectAns'}]},
{'Which spell does Ginny have a reputation for being good at?':[{'The Summoning Charm':'WrongAns'},{'Bat-Bogey Hex':'CorrectAns'},{'Jelly Legs Jinx':'WrongAns'},{'The Killing Curse':'WrongAns'}]},
{'What spell does Harry use in the first task of the Triwizard Tournament?':[{'The Killing Curse':'WrongAns'},{'Bat Bogey Hex':'WrongAns'},{'The Patronus Charm':'WrongAns'},{'The Summoning Charm':'CorrectAns'}]},
{'The Patronus Charm is used to defeat what?':[{'Lord Voldemort':'WrongAns'},{'Dementors':'CorrectAns'},{'Boggarts':'WrongAns'},{'Goblins':'WrongAns'}]},
{'What is the first transfiguration students attempt?':[{'Ravens into goblets':'WrongAns'},{'Matchsticks into needles':'CorrectAns'},{'Quill into ink':'WrongAns'},{'Conjuring water':'WrongAns'}]},
{'The Aguamenti incantation conjures what?':[{'Gold':'WrongAns'},{'Wine':'WrongAns'},{'Water':'CorrectAns'},{'Fire':'WrongAns'}]},
{'What spell is Harry Potter the only known survivor of?':[{'Wingardium Leviosa':'WrongAns'},{'Expecto Patronum':'WrongAns'},{'Crucio':'WrongAns'},{'Avada Kedavra':'CorrectAns'}]},
{'What is the most powerful truth potion?':[{'Veritaserum':'CorrectAns'},{'Amortentia':'WrongAns'},{'Polyjuice':'WrongAns'},{'Elixir of Life':'WrongAns'}]},
{'The Philosophers Stone allows for the creation of?':[{'Polyjuice Potion':'WrongAns'},{'Skelgrow':'WrongAns'},{'Firewhiskey':'WrongAns'},{'Elixir of Life':'CorrectAns'}]},
{'Where would you look for a Bezoar?':[{'Draco Malfoy\'s hair':'WrongAns'},{'Foot of a Troll':'WrongAns'},{'Stomach of a Goat':'CorrectAns'},{'Wings of a Hippogriff':'WrongAns'}]},
{'What spell does Lockhart attempt to curse Harry and Ron with but backfires?':[{'Killing curse':'WrongAns'},{'Memory Charm':'CorrectAns'},{'Stunning Spell':'WrongAns'},{'Bat Bogey Hex':'WrongAns'}]},
{'Which plant is one of the obstacles guarding the Philosopher\'s Stone?':[{'Devil\'s Snare':'CorrectAns'},{'Mandrake':'WrongAns'},{'Fanged Geranium':'WrongAns'},{'Puffapod':'WrongAns'}]},
{'Which potion do Harry, Ron and Hermione use to sneak into the Slytherin House common room in The Chamber of Secrets?':[{'Draught of Living Death':'WrongAns'},{'Wolfsbane Potion':'WrongAns'},{'Polyjuice Potion':'CorrectAns'},{'Murtlap Essence':'WrongAns'}]},
{'Which Potion does Horace Slughorn award to Harry in his sixth year at Hogwarts?':[{'Babbling Beverage':'WrongAns'},{'Felix Felicis':'CorrectAns'},{'Essence of Dittany':'WrongAns'},{'Invisibility Potion':'WrongAns'}]},
{'What is the effect of Essence of Dittany?':[{'Regrow skin over a wound':'CorrectAns'},{'Extend the taker\'s life':'WrongAns'},{'Relieve anxiety':'WrongAns'},{'Remove acne':'WrongAns'}]},
{'What is the effect of the spell that Ron attempts to curse Malfoy with in Harry Potter and the Chamber of Secrets?':[{'He vomits slugs':'CorrectAns'},{'He gets knocked out':'WrongAns'},{'He loses his memory':'WrongAns'},{'He vanishes his own bones':'WrongAns'}]},
{'Which of these cannot be conjured?':[{'Food':'CorrectAns'},{'Flames':'WrongAns'},{'Christmas Decorations':'WrongAns'},{'Shackles':'WrongAns'}]},
{'In what year to Hogwarts students learn to Apparate?':[{'5th year':'WrongAns'},{'4th year':'WrongAns'},{'3rd year':'WrongAns'},{'6th year':'CorrectAns'}]},
{'What type of creatures pull the carriages from the Hogwarts Express up to Hogwarts?':[{'Thestrals':'CorrectAns'},{'Dragons':'WrongAns'},{'Unicorns':'WrongAns'},{'Horses':'WrongAns'}]},
{'What is the effect of consuming Unicorn blood?':[{'Extended life':'CorrectAns'},{'Shrunken head':'WrongAns'},{'Eternal happiness':'WrongAns'},{'No effect':'WrongAns'}]},
{'When is the trace lifted?':[{'At age 17':'CorrectAns'},{'At age 18':'WrongAns'},{'After graduating from Hogwarts':'WrongAns'},{'After cursing yourself':'WrongAns'}]},
{'How to Fred and George attempt to trick the Goblet of Fire in to accepting their names?':[{'Ageing Potion':'CorrectAns'},{'Get a friend to submit their names':'WrongAns'},{'Levitate their names into the goblet':'WrongAns'},{'Change their birthdays':'WrongAns'}]},
{'Why are Mandrakes dangerous?':[{'Scream can kill a human':'CorrectAns'},{'They have sharp teeth':'WrongAns'},{'They shoot poisonous goo':'WrongAns'},{'They release toxic fumes':'WrongAns'}]},
{'What is the effect of the spell Hagrid casts on Dudley in the first novel?':[{'He grows a tail':'CorrectAns'},{'He dies':'WrongAns'},{'He grows an extra foot':'WrongAns'},{'He grows ears':'WrongAns'}]},
{'What spell can Witches and Wizards use to produce light?':[{'Lumos':'CorrectAns'},{'Lumio':'WrongAns'},{'Lome':'WrongAns'},{'Expelliarmus':'WrongAns'}]},
{'How does Dumbledore enforce the age restriction imposed on the Triwizard Tournament?':[{'Age Line around the Goblet':'CorrectAns'},{'Filch guards the Goblet':'WrongAns'},{'Disillusionment Charm to hide the Goblet':'WrongAns'},{'Circle of flames around the Goblet':'WrongAns'}]},
{'What creature attacks Draco in Hagrid\'s Care of Magical Creatures class?':[{'Hippogriff':'CorrectAns'},{'Acromantula':'WrongAns'},{'Dragon':'WrongAns'},{'Troll':'WrongAns'}]},
{'Which Hogwarts course is taught by a ghost?':[{'History of Magic':'CorrectAns'},{'Charms':'WrongAns'},{'Transfiguration':'WrongAns'},{'Divination':'WrongAns'}]},
{'In their fourth year at Hogwarts, what creature did students raise as a project throughout the year?':[{'Blast-Ended Skrewts':'CorrectAns'},{'Nifflers':'WrongAns'},{'Bowtruckles':'WrongAns'},{'Fire crabs':'WrongAns'}]},
{'What Christmas present does Harry recieve annonymously in his first year at Hogwarts?':[{'Invisibility Cloak':'CorrectAns'},{'Bertie Bott\'s Every Flavour Beans':'WrongAns'},{'Chocolate Frogs':'WrongAns'},{'Elder Wand':'WrongAns'}]},
{'Which of these is not a core course in the Hogwarts syllabus?':[{'Divination':'CorrectAns'},{'History of Magic':'WrongAns'},{'Herbology':'WrongAns'},{'Charms':'WrongAns'}]},
{'What is a dangerous side-effect that can happen when Apparating?':[{'Splinching':'CorrectAns'},{'Memory Loss':'WrongAns'},{'Dementia':'WrongAns'},{'Dragon Pox':'WrongAns'}]},
{'What type of spell is the one that spreads through Dumbledore\'s finger?':[{'Curse':'CorrectAns'},{'Hex':'WrongAns'},{'Jinx':'WrongAns'},{'Charm':'WrongAns'}]},
{'What creatures guard the Wizard prison, Askaban?':[{'Dementors':'CorrectAns'},{'Dragons':'WrongAns'},{'Bowtruckles':'WrongAns'},{'Giants':'WrongAns'}]},
{'What is the effect of a Dementor\'s Kiss?':[{'Loss of Soul':'CorrectAns'},{'Death':'WrongAns'},{'Euphoria':'WrongAns'},{'Pain':'WrongAns'}]},
{'Which Unforgivable Curse(s) does Harry use?':[{'Imperio and Crucio':'CorrectAns'},{'Imperio, Crucio, and Avada Kedavra':'WrongAns'},{'Avada Kedavra':'WrongAns'},{'He never uses an Unforgivable curse':'WrongAns'}]},
{'How does the Sorting Hat aid Harry in the Chamber of Secrets?':[{'It kills the Basilisk':'WrongAns'},{'It presents him with Gryffindor\'s sword':'CorrectAns'},{'It pokes out the Basilisk\'s eye':'WrongAns'},{'It shouts words of encouragement':'WrongAns'}]},
{'What do Ron and Hermione find in the Chamber of Secrets that can kill Horcruxes?':[{'Sword of Gryffindor Fangs':'WrongAns'},{'Basilisk Fangs':'CorrectAns'},{'Stinging Nettles':'WrongAns'},{'Blood-Soaked Dagger':'WrongAns'}]},
{'What deed must one perform to create a Horcrux?':[{'Throw a party':'WrongAns'},{'Give a blood sacrifice':'WrongAns'},{'Love Someone':'WrongAns'},{'Murder Someone':'CorrectAns'}]},
{'Which of these is not one of Voldemort\'s Horcruxes?':[{'Snape\'s Potions Textbook':'CorrectAns'},{'Tom Riddle\'s Diary':'WrongAns'},{'Gaunt\'s Ring':'WrongAns'},{'Slytherin\'s Locket':'WrongAns'}]},
{'What is the consequence of breaking an unbreakable vow?':[{'You\'re Cursed':'WrongAns'},{'You Shrink':'WrongAns'},{'You Die':'CorrectAns'},{'You Disappear':'WrongAns'}]},
{'What spell does Hermione use to set a flock of birds on Ron?':[{'Avis':'CorrectAns'},{'Avifors':'WrongAns'},{'Avios':'WrongAns'},{'Avifo':'WrongAns'}]},
{'Which charm, which enforces the Hogsmeade curfew, produces a loud screech when someone steps into it\'s radius?':[{'Bubble-Head Charm':'WrongAns'},{'Revealing Charm':'WrongAns'},{'Caterwauling Charm':'CorrectAns'},{'Intruder Charm':'WrongAns'}]},
{'Which spell does Hermione cast to freeze the pixies in Professor Lockhart\'s class?':[{'Impedimenta':'WrongAns'},{'Immobolus':'CorrectAns'},{'Inanimatus Conjurus':'WrongAns'},{'Incarcerous':'WrongAns'}]},
{'Which spell does Dumbledore use to save Harry when he falls off his broom during a Quidditch match?':[{'Ascendio':'WrongAns'},{'Anteoculatia':'WrongAns'},{'Aresto Momentum':'CorrectAns'},{'Baubillious':'WrongAns'}]},
{'The curse whose incantation is \"Mucus ad Nauseam\" has what effect on it\'s target?':[{'Enlarged ears':'WrongAns'},{'Lack of airflow to lungs':'WrongAns'},{'A massive headache':'WrongAns'},{'An extremely runny nose':'CorrectAns'}]},
{'Depulso (Banishing charm) has the opposite effect to which spell?':[{'Crucio':'WrongAns'},{'Accio':'CorrectAns'},{'Defodio':'WrongAns'},{'Confringo':'WrongAns'}]},
{'Which spell causes the target to swell in physical size?':[{'Entomorphis':'WrongAns'},{'Engorgio':'CorrectAns'},{'Evanesce':'WrongAns'},{'Incarcerous':'WrongAns'}]},
{'Locomotor Wibbly is known by what other name?':[{'Jelly-Fingers Curse':'WrongAns'},{'Jelly-Brain Jinx':'WrongAns'},{'Jelly-Legs Curse':'CorrectAns'},{'Jelly-Arms Curse':'WrongAns'}]},
{'What spell does James Potter cast on Severus Snape in his teenage years, that levitates Snape upside-down by his ankles?':[{'Liberacorpus':'WrongAns'},{'Wingardium-Corpus':'WrongAns'},{'Levicorpus':'CorrectAns'},{'Corpus-Leviosa':'WrongAns'}]},
{'What curse prevents witches and wizards from discussing the location of Grimmault place, when it acts as the headquarters for the Order?':[{'Tongue-Tying Curse':'CorrectAns'},{'Full Body-Bind Curse':'WrongAns'},{'Reductor Curse':'WrongAns'},{'Conjunctivitis Curse':'WrongAns'}]},
{'Which potion does Harry brew in Slughorn\'s class to win a vial of Felix Felicis?':[{'Draught of Dying':'WrongAns'},{'Draught of Living Death':'CorrectAns'},{'Lifeless Draught':'WrongAns'},{'Invigoration Draught':'WrongAns'}]},
{'Wolfsbane potion eases the symptoms of what?':[{'Rhumanthropy':'WrongAns'},{'Tyronthropy':'WrongAns'},{'Lycanthropy':'CorrectAns'},{'Ayanthropy':'WrongAns'}]},
{'Which potion did Voldemort use to protect Salazar Slytherin\'s locket (a horcrux)?':[{'Dogbane Potion':'WrongAns'},{'Baneberry Poision':'WrongAns'},{'Dragon Poison':'WrongAns'},{'Drink of Despair':'CorrectAns'}]},
{'At the start of the Quidditch World Cup, which spell does Bagman use to increase the volume of his voice as he announces the game?':[{'Sonorus':'CorrectAns'},{'Amplifie':'WrongAns'},{'Incantum Sonar':'WrongAns'},{'Volum Maxima':'WrongAns'}]},
{'Which spell, which caused her to grow antlers, was used on Pansy Parkinson during a student rebellion after Fred and George\'s departure from Hogwarts?':[{'Aparceium':'WrongAns'},{'Antleroneo':'WrongAns'},{'Antlamoria':'WrongAns'},{'Anteoculatia':'CorrectAns'}]},
{'Which spell blasts away arachnids?':[{'Arania Expulso':'WrongAns'},{'Arania Exumai':'CorrectAns'},{'Arachnia Expulso':'WrongAns'},{'Arachnia Aspiria':'WrongAns'}]},
{'Lockhart unsuccessfuly tries to fix Harry\'s broken arm after he falls from his broom with which spell?':[{'Brackium Emendo':'CorrectAns'},{'Skele-Gro':'WrongAns'},{'Corpio Mendes':'WrongAns'},{'Skeleta Engorgio':'WrongAns'}]},
{'Which of these charms is NOT included in Harry\'s OWL exam for Charms.':[{'Levitation Charm':'WrongAns'},{'Cheering Charm':'WrongAns'},{'Cushioning Charm':'CorrectAns'},{'Color Change Charm':'WrongAns'}]},
{'What did Crabbe conjure in the final novel that ultimately resulted in his death?':[{'Firestorm':'WrongAns'},{'Fiendfyre':'CorrectAns'},{'Bewitched Snowballs':'WrongAns'},{'Bluebell flames':'WrongAns'}]},
{'What charm did medieval witches use to protect themselves during witch burnings?':[{'Flame-Repelling Charm':'WrongAns'},{'Flame-Freezing Charm':'CorrectAns'},{'Flame-Protection Charm':'WrongAns'},{'Fire-Extinguishing Charm':'WrongAns'}]},
{'Which spell does Hermione use to detect the presence of humans in Grimmauld place?':[{'Homeorevel':'WrongAns'},{'Homenum Expelia':'WrongAns'},{'Homeosape Revel':'WrongAns'},{'Homenum Revelio':'CorrectAns'}]},
{'The Impervius Charm has what effect?':[{'It makes doors impenetrable':'WrongAns'},{'It makes the target cry':'WrongAns'},{'It repels substance':'CorrectAns'},{'It controls the mind':'WrongAns'}]},
{'In Harry\'s private lessons with Professor Snape, what is he learning to protect himself against?':[{'The Imperio Curse':'WrongAns'},{'Legilimency':'CorrectAns'},{'Voldemort\'s Horcrux':'WrongAns'},{'Prior Incantato':'WrongAns'}]},
{'What is the name of the magical phenomenon that occurs when two wands that share the same core are forced to compete in combat?':[{'Priorita Incantem':'WrongAns'},{'Prioincantema':'WrongAns'},{'Priori Incantatem':'CorrectAns'},{'Prior Incantato':'WrongAns'}]},
{'What spell is used to make the target release whatever it is holding or binding?':[{'Rennervate':'WrongAns'},{'Relashio':'CorrectAns'},{'Reparifors':'WrongAns'},{'Reducto':'WrongAns'}]},
{'Rennervate reverses the effects of what?':[{'Being Tired':'WrongAns'},{'Being Disfigured':'WrongAns'},{'Being Burned':'WrongAns'},{'Being Stunned':'CorrectAns'}]},
{'Rictusempra induces what sensation?':[{'Sleeping':'WrongAns'},{'Laughing':'WrongAns'},{'Smiling':'WrongAns'},{'Tickling':'CorrectAns'}]},
{'Which hex does Hermione cast on Harry to hide his true identity from the snatchers?':[{'Bedazzling Hex':'WrongAns'},{'Bat-Bogey Hex':'WrongAns'},{'Stinging Hex':'CorrectAns'},{'Hurling Hex':'WrongAns'}]},
{'Which curse showed the snatchers the location of Harry Potter in the Second Wizarding War?':[{'The Ear-Shrivelling Curse':'WrongAns'},{'The Babbling Curse':'WrongAns'},{'The Taboo Curse':'CorrectAns'},{'The Imperius Curse':'WrongAns'}]},
{'In Harry\'s final transfiguration exam of his third year at Hogwarts, which transforming spell is he required to perform?':[{'Raven to Writing Desk':'WrongAns'},{'Snail to Teapot':'WrongAns'},{'Human to Chicken':'WrongAns'},{'Teapot to Tortoise':'CorrectAns'}]},
{'Which of these is not a piece of security in Gringotts?':[{'Veritaserum':'CorrectAns'},{'The Gemino Charm':'WrongAns'},{'A Dragon':'WrongAns'},{'The Thief\'s Downfall':'WrongAns'}]},
{'What is the incantation to transform an animal into a water goblet?':[{'Vero Verta':'WrongAns'},{'Vera Verto':'CorrectAns'},{'Piertotum Locomotor':'WrongAns'},{'Vipera Evanesca':'WrongAns'}]},
{'Which of these love potions is the strongest?':[{'Twilight Moonbeams':'WrongAns'},{'Beguiling Bubbles':'WrongAns'},{'Amortentia':'CorrectAns'},{'Cupid Crystals':'WrongAns'}]},
{'Which of these creatures was not part of Professor Lupin\'s curriculum when he taught Defense Against the Dark Arts at Hogwarts?':[{'Grindylows':'WrongAns'},{'Hinkypunks':'WrongAns'},{'Cornish Pixies':'CorrectAns'},{'Vampires':'WrongAns'}]},
{'What happens when Bubotuber pus comes in contact with human skin?':[{'Burns your skin':'WrongAns'},{'Sticks to your skin':'WrongAns'},{'A rash forms':'WrongAns'},{'Boils appear':'CorrectAns'}]},
{'Mimbulus Mimbletonia spews what when touched?':[{'Bubotuber Pus':'WrongAns'},{'Stinksap':'CorrectAns'},{'Draught of Living Death':'WrongAns'},{'Elixir of Life':'WrongAns'}]},
{'Which of these tree\'s wood is not used in the making of wands':[{'Oak':'WrongAns'},{'Yew':'WrongAns'},{'Cherry':'WrongAns'},{'Palm':'CorrectAns'}]},
{'Which of these dragons was not in the Triwizard Tournament?':[{'Norweigan Ridgeback':'WrongAns'},{'Common Welsh Creen':'WrongAns'},{'Ukranian Ironbelly':'CorrectAns'},{'Hungarian Horntail':'WrongAns'}]},
{'What do niffler\'s sniff out?':[{'Wands':'WrongAns'},{'Lava Rocks':'WrongAns'},{'Dead Wizards':'WrongAns'},{'Shiny Treasure':'CorrectAns'}]},
{'What piece of jewellery holds the curse that hits Katie Bell when she touches it?':[{'Anklet':'WrongAns'},{'Ring':'WrongAns'},{'Necklace':'CorrectAns'},{'Bracelet':'WrongAns'}]},
{'How does Umbridge torture her students in detention?':[{'A Blood Quill':'CorrectAns'},{'She Curses Them':'WrongAns'},{'She Hits Them':'WrongAns'},{'Crucio':'WrongAns'}]},
{'What charm does Hermione use to expand the space available inside her handbag in the Deathly Hallows?':[{'Expanding Space Charm':'WrongAns'},{'Undetectable Extension Charm':'CorrectAns'},{'Increased Area Charm':'WrongAns'},{'Never-Full Charm':'WrongAns'}]},
{'Which spell does Harry use to fill Dumbledore\'s crystal goblet with water in the Horcrux cave?':[{'Aquamenta':'WrongAns'},{'Aguamenti':'CorrectAns'},{'Agua-Conjurus':'WrongAns'},{'Agua Eructo':'WrongAns'}]},
{'What spell does James Potter use on Severus Snape that prevents Snape from moving towards James?':[{'Protego Horribilis':'WrongAns'},{'Mobiliarbus':'WrongAns'},{'Locomotor Wibbly':'WrongAns'},{'Impedimenta':'CorrectAns'}]},
{'What is the incantation for the spell that Lockhart unsuccessfuly uses to get rid of the pixies in his classrom?':[{'Peskipsi Postoni':'WrongAns'},{'Peski Pixies Nomi':'WrongAns'},{'Piksi Pestroni':'WrongAns'},{'Peskipiksi Pesternomi':'CorrectAns'}]},
{'Which charm fills the ears of anyone in the vicinity with a buzzing noise?':[{'Fidelius Charm':'WrongAns'},{'Caterwauling Charm':'WrongAns'},{'Muffliato Charm':'CorrectAns'},{'Homorphus Charm':'WrongAns'}]},
{'Which spell does Lockhart use unsuccessfully during duelling club to banish the snake that has been set on Harry?':[{'Crucio':'WrongAns'},{'Alarte Ascendare':'CorrectAns'},{'Confringo':'WrongAns'},{'Defodio':'WrongAns'}]},
{'Which spell does Horace Slughorn use on Marcus Belby to clear his airway while choking on pheasant?':[{'Ascenda Oesophago':'WrongAns'},{'Anteoculatia':'WrongAns'},{'Anapneo':'CorrectAns'},{'Arania Eructo':'WrongAns'}]},
{'Which spell does Ollivander use to test Fleur\'s wand before the Tri-Wizard Tournament?':[{'Muffliato':'WrongAns'},{'Lumos':'WrongAns'},{'Deletrius':'WrongAns'},{'Orchideous':'CorrectAns'}]},
{'What is the twelfth use of Dragon\'s Blood?':[{'Curing Wounds':'WrongAns'},{'Immortality':'WrongAns'},{'Deadly Poison':'WrongAns'},{'Oven Cleaning':'CorrectAns'}]},
{'According to Luna, Gurdyroot is effective at warding off what?':[{'Crumple-Horned Snorkack':'WrongAns'},{'Gulping Plimpies':'CorrectAns'},{'Wrackspurts':'WrongAns'},{'Dabberblimps':'WrongAns'}]},
{'What is not an ingredient in Polyjuice potion?':[{'Boomslang Skin':'WrongAns'},{'Lacewing Flies':'WrongAns'},{'Aconite':'CorrectAns'},{'Bicorn Horn':'WrongAns'}]},
{'What is a characteristic of Amortenia?':[{'Clear and Odourless appearance':'WrongAns'},{'Heart shaped smoke':'WrongAns'},{'Sweet Smell':'WrongAns'},{'Mother of Pearl Sheen':'CorrectAns'}]},
{'Which is not an ingredient used by Voldemort to create himself a new body?':[{'Bone of the his father':'WrongAns'},{'Heart of his mother':'CorrectAns'},{'Flesh of a servant':'WrongAns'},{'Blood of an enemy':'WrongAns'}]},
{'What spell did Hermione not cast over the trios tent in the 7th book?':[{'Salvio Hexia':'WrongAns'},{'Protego Totalum':'WrongAns'},{'Repello Muggletum':'WrongAns'},{'Protego Maxima':'CorrectAns'}]},
{'What was the initial enchantment used by Voldemort to protect his Horcrux in the cave?':[{'Inferi':'WrongAns'},{'Blood Sacrifice':'CorrectAns'},{'Fidelius charm':'WrongAns'},{'Warded':'WrongAns'}]},
{'What incantation causes duplication of an object?':[{'Polygrate':'WrongAns'},{'Multiplus':'WrongAns'},{'Geminio':'CorrectAns'},{'Duplicato':'WrongAns'}]},
{'What incantation conjures a fiery rope?':[{'Flagrate':'CorrectAns'},{'Incendiope':'WrongAns'},{'Avis':'WrongAns'},{'Dormiens':'WrongAns'}]},
{'What is the incantation for the vanishing spell?':[{'Revoir':'WrongAns'},{'Fleum':'WrongAns'},{'Vanishia':'WrongAns'},{'Evanesco':'CorrectAns'}]},
{'How long does Felix Felicis take to brew?':[{'1 year':'WrongAns'},{'1 month':'WrongAns'},{'6 months':'CorrectAns'},{'4 months':'WrongAns'}]},
{'How many shades appear out of Voldemort\'s wand in Priori Incantatem?':[{'3':'WrongAns'},{'4':'WrongAns'},{'5':'CorrectAns'},{'6':'WrongAns'}]},
{'What creature did Tom Riddle accuse Hagrid of raising and using to petrify students when the Chamber of Secrets was first opened?':[{'Dragon':'WrongAns'},{'Basilisk':'WrongAns'},{'Acromantula':'CorrectAns'},{'Fire Crab':'WrongAns'}]},
{'What creature is commonly found in wand-wood trees?':[{'Crumple Horned Snorkack':'WrongAns'},{'Phoenix':'WrongAns'},{'Augury':'WrongAns'},{'Bowtruckle':'CorrectAns'}]},
{'What horn was present on the wall of Xenophilius\'s Lovegood\'s house?':[{'Crumple Horned Snorkack':'WrongAns'},{'Erumpent':'CorrectAns'},{'Unicorn':'WrongAns'},{'Graphorn':'WrongAns'}]},
{'Where did Professor Snape claim the Kappa is most commonly found?':[{'Russia':'WrongAns'},{'China':'WrongAns'},{'Mongolia':'CorrectAns'},{'Japan':'WrongAns'}]},
{'Where is a Kappa most commonly found?':[{'Japan':'CorrectAns'},{'Mongolia':'WrongAns'},{'China':'WrongAns'},{'Korea':'WrongAns'}]},
{'What is the opposite of the Alohamora spell?':[{'Closaportus':'WrongAns'},{'Clauditis':'WrongAns'},{'Alohimara':'WrongAns'},{'Colloportus':'CorrectAns'}]},
{'What spell causes rapid growth of the victims teeth?':[{'Depulso':'WrongAns'},{'Growtio':'WrongAns'},{'Densaugeo':'CorrectAns'},{'Denturio':'WrongAns'}]},
{'What spell did Bagman use to cancel Sonorus at the Quidditch World Cup?':[{'Finite Incantatum':'WrongAns'},{'Finite':'WrongAns'},{'Quietus':'CorrectAns'},{'Silencio':'WrongAns'}]},
{'What is the counter to Levicorpus':[{'Liberacorpus':'CorrectAns'},{'Finite':'WrongAns'},{'Collocorpus':'WrongAns'},{'Dissendium':'WrongAns'}]},
{'What is an ingredient Hermione uses when creating an antidote to an unknown poison in 6th year?':[{'Her blood':'WrongAns'},{'Her own hair':'CorrectAns'},{'A Bezoar':'WrongAns'},{'Boomslang skin':'WrongAns'}]},
{'The Dreamless sleep potion is what when taken regularly?':[{'No effect':'WrongAns'},{'Less effective':'WrongAns'},{'Poisonus':'WrongAns'},{'Addictive':'CorrectAns'}]},
]

# chatterbot = ChatBot("Harry Botter")
# chatterbot.set_trainer(ChatterBotCorpusTrainer)
# chatterbot.train(
#     "chatterbot.corpus.english"
# )
class House(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    members_num = db.Column(db.Integer)
    points = db.Column(db.Integer)

    def __init__(self, name):
        self.name = name
        self.points = 0
        self.members_num =0

    def update_score(self,points):
        self.points += points

    def update_members(self):
        self.members_num += 1

class Shared_with(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.String(80))
    shared_with_id = db.Column(db.String(80))

    def __init__(self, sender_id,shared_with_id):
        self.sender_id = sender_id
        self.shared_with_id =shared_with_id


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), unique=True)
    house = db.Column(db.String(120))
    q1 = db.Column(db.String(80))
    q2 = db.Column(db.String(80))
    q3 = db.Column(db.String(80))
    q4 = db.Column(db.String(80))
    q5 = db.Column(db.String(80))
    points = db.Column(db.Integer)
    last_day_seen = db.Column(db.String(80))
    created_at = db.Column(db.DateTime)


    def __init__(self, user_id):
        self.user_id = user_id
        self.points = 0
        self.created_at = datetime.utcnow()

    def update_score(self,points):
        self.points += points

    def get_q1(self):
        return self.q1

    def get_q2(self):
        return self.q2

    def get_q3(self):
        return self.q3

    def get_q4(self):
        return self.q4

    def get_q5(self):
        return self.q5

    def get_house(self):
        return self.house

# all_users = User.query.all()

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
# FB.set_menu()
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
dbAPI.addHouses(db)
# dbAPI.resetPoints(db)
# dbAPI.deleteUser(db,'1139478602829591')
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
    try:
        if data["object"] == "page":

            for entry in data["entry"]:
                for messaging_event in entry["messaging"]:
                    if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                        sender_id = messaging_event["sender"]["id"]  # the facebook ID of the person sending you the message
                        handleEveryDayPoints(db, sender_id)
                        recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                        message_payload = messaging_event["postback"]["payload"]
                        if messaging_event["postback"].get("referral"):
                            message_ref = messaging_event["postback"]["referral"]["ref"]
                            reply = message_ref.split(',')
                            if reply[0] == 'Harry_Botter_Add_Share_Points':
                                handleShare(db, reply[1],sender_id)
                            print 'Reeeeeeeeeeef is ' + str(message_ref)
                        user = FB.get_user_fb(token,sender_id)
                        print 'Message Payload is '+ str(message_payload)
                        if message_payload == "Harry_Botter_Help":
                            handle_help(sender_id)
                            FB.send_quick_replies_help(token, sender_id, '...')
                        elif message_payload == "Harry_Botter_Get_Started":
                            handle_first_time_user(db,sender_id,user)

                        elif message_payload == "Harry_Botter_Characters":
                            handle_characters(sender_id)

                        elif message_payload == "Harry_Botter_House":
                            FB.show_typing(token, sender_id, 'typing_off')
                            handleViewHouse(db, sender_id)



                        elif message_payload == "Harry_Botter_Spells":
                            handle_spells(sender_id)

                        elif message_payload == "Harry_Botter_Places":
                            handle_places(sender_id)

                        elif message_payload == "Harry_Botter_SortHat":
                            FB.show_typing(token, sender_id, 'typing_off')
                            handleSortingHat(db, sender_id)

                        elif message_payload == "Harry_Botter_Trivia_Question":
                            FB.show_typing(token, sender_id, 'typing_off')
                            handleTrivia(db, sender_id)

                        elif message_payload == "Harry_Botter_Profile":
                            FB.show_typing(token, sender_id, 'typing_off')
                            handleProfile(db, sender_id)


                        elif message_payload == "Harry_Botter_Houses":
                            FB.show_typing(token, sender_id, 'typing_off')
                            handleViewHouses(db, sender_id)


                        elif message_payload == "Harry_Botter_LeaderBoard":
                            FB.show_typing(token, sender_id, 'typing_off')
                            handleLeaderBoard(db, sender_id)
                            GreateHallReplies(sender_id)

                        elif message_payload == "Harry_Botter_Share":
                            FB.show_typing(token, sender_id, 'typing_off')
                            sortHatResult(sender_id)


                        elif message_payload == "Harry_Botter_Get_Points":
                            FB.show_typing(token, sender_id, 'typing_off')
                            getpoints(sender_id)

                        elif message_payload == "Harry_Botter_License":
                            FB.show_typing(token, sender_id, 'typing_off')
                            handleLicense(sender_id)


                        elif message_payload == "character-harry-potter":
                            sendFromQuickReply(sender_id,'Harry Potter')
                        elif message_payload == "character-ron-weasley":
                            sendFromQuickReply(sender_id,'Ron Weasley')
                        elif message_payload == "character-hermione-granger":
                            sendFromQuickReply(sender_id,'hermione granger')
                        elif message_payload == "character-albus-dumbledore":
                            sendFromQuickReply(sender_id,'albus dumbledore')

                        elif message_payload == "spell-aguamenti":
                            sendFromQuickReply(sender_id,'aguamenti')
                        elif message_payload == "spell-expecto-patronum":
                            sendFromQuickReply(sender_id,'expecto patronum')
                        elif message_payload == "spell-avada-kedavra":
                            sendFromQuickReply(sender_id,'avada-kedavra')
                        elif message_payload == "spell-alohomora":
                            sendFromQuickReply(sender_id,'alohomora')

                        elif message_payload == "place-diagon-alley":
                            sendFromQuickReply(sender_id,'diagon alley')
                        elif message_payload == "place-godric-hollow":
                            sendFromQuickReply(sender_id,'godric\'s hollow')
                        elif message_payload == "place-hogsmeade":
                            sendFromQuickReply(sender_id,'hogsmeade')
                        elif message_payload == "place-hogwarts-express":
                            sendFromQuickReply(sender_id,'hogwarts express')


                    if messaging_event.get("referral"):
                        sender_id = messaging_event["sender"]["id"]
                        message_ref = messaging_event["referral"]["ref"]
                        reply = message_ref.split(',')
                        if reply[0] == 'Harry_Botter_Add_Share_Points':
                            handleShare(db, reply[1], sender_id)

                    print 'Messaging Event is '+ str(messaging_event)
                    if messaging_event.get("message"):  # someone sent us a message
                        sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                        handleEveryDayPoints(db,sender_id)
                        recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                        message = messaging_event["message"]  # the message's text
                        if messaging_event.get("referral"):
                            message_ref = messaging_event["referral"]["ref"]
                            reply = message_ref.split(',')
                            if reply[0]=='Harry_Botter_Add_Share_Points':
                                handleShare(db,reply[1],sender_id)
                            print 'Reeeeeeeeeeef is ' + str(message_ref)
                        print 'Heeeeeeeeeeeeeeeere '+ str(messaging_event['message'].get('quick_reply'))
                        if messaging_event['message'].get('quick_reply'):
                            message_payload = messaging_event['message']['quick_reply']['payload']
                            if message_payload == "Q1_H":
                                user = User.query.filter_by(user_id=sender_id).first()
                                if user:
                                    user.q1 = 'H'
                                    db.session.commit()
                                    handleSortingHat(db, sender_id)
                            elif message_payload == "Q1_G":
                                user = User.query.filter_by(user_id=sender_id).first()
                                if user:
                                    user.q1 = 'G'
                                    db.session.commit()
                                    handleSortingHat(db, sender_id)
                            elif message_payload == "Q1_R":
                                user = User.query.filter_by(user_id=sender_id).first()
                                if user:
                                    user.q1 = 'R'
                                    db.session.commit()
                                    handleSortingHat(db, sender_id)
                            elif message_payload == "Q1_S":
                                user = User.query.filter_by(user_id=sender_id).first()
                                if user:
                                    user.q1 = 'S'
                                    db.session.commit()
                                    handleSortingHat(db, sender_id)

                            elif message_payload == "Q2_H":
                                user = User.query.filter_by(user_id=sender_id).first()
                                if user:
                                    user.q2 = 'H'
                                    db.session.commit()
                                    handleSortingHat(db, sender_id)
                            elif message_payload == "Q2_G":
                                user = User.query.filter_by(user_id=sender_id).first()
                                if user:
                                    user.q2 = 'G'
                                    db.session.commit()
                                    handleSortingHat(db, sender_id)
                            elif message_payload == "Q2_R":
                                user = User.query.filter_by(user_id=sender_id).first()
                                if user:
                                    user.q2 = 'R'
                                    db.session.commit()
                                    handleSortingHat(db, sender_id)
                            elif message_payload == "Q2_S":
                                user = User.query.filter_by(user_id=sender_id).first()
                                if user:
                                    user.q2 = 'S'
                                    db.session.commit()
                                    handleSortingHat(db, sender_id)

                            elif message_payload == "Q3_H":
                                user = User.query.filter_by(user_id=sender_id).first()
                                if user:
                                    user.q3 = 'H'
                                    db.session.commit()
                                    handleSortingHat(db, sender_id)
                            elif message_payload == "Q3_G":
                                user = User.query.filter_by(user_id=sender_id).first()
                                if user:
                                    user.q3 = 'G'
                                    db.session.commit()
                                    handleSortingHat(db, sender_id)
                            elif message_payload == "Q3_R":
                                user = User.query.filter_by(user_id=sender_id).first()
                                if user:
                                    user.q3 = 'R'
                                    db.session.commit()
                                    handleSortingHat(db, sender_id)
                            elif message_payload == "Q3_S":
                                user = User.query.filter_by(user_id=sender_id).first()
                                if user:
                                    user.q3 = 'S'
                                    db.session.commit()
                                    handleSortingHat(db, sender_id)

                            elif message_payload == "Q4_H":
                                user = User.query.filter_by(user_id=sender_id).first()
                                if user:
                                    user.q4 = 'H'
                                    db.session.commit()
                                    handleSortingHat(db, sender_id)
                            elif message_payload == "Q4_G":
                                user = User.query.filter_by(user_id=sender_id).first()
                                if user:
                                    user.q4 = 'G'
                                    db.session.commit()
                                    handleSortingHat(db, sender_id)
                            elif message_payload == "Q4_R":
                                user = User.query.filter_by(user_id=sender_id).first()
                                if user:
                                    user.q4 = 'R'
                                    db.session.commit()
                                    handleSortingHat(db, sender_id)
                            elif message_payload == "Q4_S":
                                user = User.query.filter_by(user_id=sender_id).first()
                                if user:
                                    user.q4 = 'S'
                                    db.session.commit()
                                    handleSortingHat(db, sender_id)

                            elif message_payload == "Q5_H":
                                user = User.query.filter_by(user_id=sender_id).first()
                                if user:
                                    user.q5 = 'H'
                                    db.session.commit()
                                    SortingResult(db, sender_id)
                            elif message_payload == "Q5_G":
                                user = User.query.filter_by(user_id=sender_id).first()
                                if user:
                                    user.q5 = 'G'
                                    db.session.commit()
                                    SortingResult(db, sender_id)
                            elif message_payload == "Q5_R":
                                user = User.query.filter_by(user_id=sender_id).first()
                                if user:
                                    user.q5 = 'R'
                                    db.session.commit()
                                    SortingResult(db, sender_id)
                            elif message_payload == "Q5_S":
                                user = User.query.filter_by(user_id=sender_id).first()
                                if user:
                                    user.q5 = 'S'
                                    db.session.commit()
                                    SortingResult(db, sender_id)
                            elif message_payload == "WrongAns":
                                handleWrongAnswer(db,sender_id)

                            elif message_payload == "CorrectAns":
                                handleCorrectAnswer(db,sender_id)

                            elif message_payload == "Harry_Botter_House":
                                FB.show_typing(token, sender_id, 'typing_off')
                                handleViewHouse(db, sender_id)



                            elif message_payload == "Harry_Botter_SortHat":
                                FB.show_typing(token, sender_id, 'typing_off')
                                handleSortingHat(db, sender_id)


                            elif message_payload == "Harry_Botter_Trivia_Question":
                                FB.show_typing(token, sender_id, 'typing_off')
                                handleTrivia(db, sender_id)

                            elif message_payload == "Harry_Botter_Profile":
                                FB.show_typing(token, sender_id, 'typing_off')
                                handleProfile(db, sender_id)


                            elif message_payload == "Harry_Botter_Houses":
                                FB.show_typing(token, sender_id, 'typing_off')
                                handleViewHouses(db, sender_id)


                            elif message_payload == "Harry_Botter_LeaderBoard":
                                FB.show_typing(token, sender_id, 'typing_off')
                                handleLeaderBoard(db, sender_id)
                                GreateHallReplies(sender_id)

                            elif message_payload == "Harry_Botter_Share":
                                FB.show_typing(token, sender_id, 'typing_off')
                                handleSortingHat(db, sender_id)


                            elif message_payload == "Harry_Botter_Get_Points":
                                FB.show_typing(token, sender_id, 'typing_off')
                                getpoints(sender_id)

                            elif message_payload == "Harry_Botter_License":
                                FB.show_typing(token, sender_id, 'typing_off')
                                handleLicense(sender_id)

                            else:
                                user = FB.get_user_fb(token, sender_id)
                                FB.show_typing(token, sender_id)
                                response, images = processIncoming(sender_id, message)
                                if response == 'help':
                                    FB.show_typing(token, sender_id, 'typing_off')
                                    handle_help(sender_id)
                                    FB.send_quick_replies_help(token, sender_id, '...')
                                elif response == 'share':
                                    FB.show_typing(token, sender_id, 'typing_off')
                                    handleSortingHat(db, sender_id)
                                elif response == 'trivia':
                                    FB.show_typing(token, sender_id, 'typing_off')
                                    handleTrivia(db, sender_id)
                                elif response == 'view profile':
                                    FB.show_typing(token, sender_id, 'typing_off')
                                    handleProfile(db, sender_id)
                                elif response == 'view houses':
                                    FB.show_typing(token, sender_id, 'typing_off')
                                    handleViewHouses(db, sender_id)
                                elif response == 'great hall':
                                    FB.show_typing(token, sender_id, 'typing_off')
                                    GreateHallReplies(sender_id)


                                elif response == 'leaderboard':
                                    FB.show_typing(token, sender_id, 'typing_off')
                                    handleLeaderBoard(db, sender_id)
                                elif response == 'characters':
                                    FB.show_typing(token, sender_id, 'typing_off')
                                    handle_characters(sender_id)
                                elif response == 'spells':
                                    FB.show_typing(token, sender_id, 'typing_off')
                                    handle_spells(sender_id)
                                elif response == 'places':
                                    FB.show_typing(token, sender_id, 'typing_off')
                                    handle_places(sender_id)
                                elif response == 'How can I help you?':
                                    FB.send_quick_replies_help(token, sender_id, 'How can I help you?')
                                else:
                                    FB.show_typing(token, sender_id, 'typing_off')
                                    FB.send_message(token, sender_id, response)
                                    if images:
                                        print 'Images here ' + str(images)
                                        FB.send_message(token, sender_id, 'Here are some pictures ;)')
                                        FB.send_group_pictures(app, token, sender_id, images)
                        else:
                            user = FB.get_user_fb(token, sender_id)
                            FB.show_typing(token, sender_id)
                            response, images = processIncoming(sender_id, message)
                            if response == 'help':
                                FB.show_typing(token, sender_id, 'typing_off')
                                handle_help(sender_id)
                                FB.send_quick_replies_help(token, sender_id, '...')
                            elif response == 'share':
                                FB.show_typing(token, sender_id, 'typing_off')
                                handleSortingHat(db, sender_id)
                            elif response == 'trivia':
                                FB.show_typing(token, sender_id, 'typing_off')
                                handleTrivia(db, sender_id)
                            elif response == 'view profile':
                                FB.show_typing(token, sender_id, 'typing_off')
                                handleProfile(db, sender_id)
                            elif response == 'view houses':
                                FB.show_typing(token, sender_id, 'typing_off')
                                handleViewHouses(db, sender_id)

                            elif response == 'leaderboard':
                                FB.show_typing(token, sender_id, 'typing_off')
                                handleLeaderBoard(db, sender_id)
                            elif response == 'characters':
                                FB.show_typing(token, sender_id, 'typing_off')
                                handle_characters(sender_id)
                            elif response == 'spells':
                                FB.show_typing(token, sender_id, 'typing_off')
                                handle_spells(sender_id)
                            elif response == 'places':
                                FB.show_typing(token, sender_id, 'typing_off')
                                handle_places(sender_id)
                            elif response == 'How can I help you?':
                                FB.send_quick_replies_help(token, sender_id, 'How can I help you?')
                            elif response == 'great hall':
                                FB.show_typing(token, sender_id, 'typing_off')
                                GreateHallReplies(sender_id)
                            else:
                                FB.show_typing(token, sender_id, 'typing_off')
                                FB.send_message(token, sender_id, response)
                                if images:
                                    print 'Images here ' + str(images)
                                    FB.send_message(token, sender_id, 'Here are some pictures ;)')
                                    FB.send_group_pictures(app,token,sender_id,images)

                    return "ok"
    except Exception, e:
        print e




    return "ok", 200

def sendFromQuickReply(sender_id,message):
    response, images = processIncoming(sender_id, message)
    if response:
        FB.show_typing(token, sender_id, 'typing_off')
        FB.send_message(token, sender_id, response)
    if images:
        print 'Images here ' + str(images)
        FB.send_message(token, sender_id, 'Here are some pictures ;)')
        FB.send_group_pictures(app, token, sender_id, images)

def processIncoming(user_id, message):
    try:

        if message.get('sticker_id'):
            return '(y)',[]
        userInput = message['text']
        userInput = userInput.lower()
        user = FB.get_user_fb(token, user_id)
        response =''
        ## TEMP: to see & verify POS tagging
        print("User Input : %s" % userInput)

        response = ''
        if userInput.lower() == 'help':
            return 'help',[]
        elif userInput.lower() == 'characters' or userInput.lower() == 'character':
            return 'characters',[]
        elif userInput.lower() == 'spells' or userInput.lower() == 'spell':
            return 'spells',[]
        elif userInput.lower() == 'share':
            return 'share',[]
        elif userInput.lower() == 'trivia':
            return 'trivia',[]
        elif userInput.lower() == 'view profile':
            return 'view profile',[]
        elif userInput.lower() == 'view houses':
            return 'view houses',[]
        elif userInput.lower() == 'leaderboard':
            return 'leaderboard',[]
        elif userInput.lower() == 'great hall':
            return 'great hall',[]
        elif userInput.lower() == 'places' or userInput.lower() == 'place':
            return 'places',[]

        if NLP.isGreetings(userInput):
            greeting = "%s %s :D" % (NLP.sayHiTimeZone(user), user['first_name'])
            FB.send_message(token, user_id, greeting)
            return "How can I help you?",[]
        elif NLP.isGoodbye(userInput):
            return NLP.sayByeTimeZone(user),[]

        if NLP.badWords(userInput):
            return 'Well I\'m not supposed to reply to that :/',[]

        if NLP.isAskingBotInformation(userInput):
            return NLP.handleBotInfo(userInput),[]

        if NLP.isEasterEggs(userInput):
            return NLP.handleEasterEggs(userInput),[]

        if NLP.isFunny(userInput):
            return NLP.oneOf(['Glad you like it :D',':D :D']),[]

        if NLP.isEmoji(userInput):
            FB.show_typing(token, user_id, 'typing_off')
            FB.send_emoji(token,user_id,NLP.handleEmoji(userInput))
            return '',[]

        if NLP.answerWithOkay(userInput):
            return 'Okay',[]
        elif NLP.isThanking(userInput):
            return NLP.oneOf(NLP.thanks_replies),[]
        elif NLP.isPraising(userInput):
            return NLP.oneOf(NLP.praise_replies),[]

        ## Perform POS-tagging on user input
        userInput = userInput.upper()
        tagged_input = pos_tag(word_tokenize(userInput))
        print("POS-Tagged User Input : %s " % tagged_input)
        intent = obtainUserIntent(tagged_input)

        if intent == Intent.QUERY:
            # print("Harry IS THINKING...")
            response,images = deviseAnswer(tagged_input)
        elif intent == Intent.NONSENSE:
            # print("Harry THINKS YOU ARE UNCLEAR.")
            images = []
            try:
                response, images = deviseNonsense(tagged_input)
            except Exception, e:
                response = "%s" % (RESPONSE_TO_NONSENSE[random.randint(0, len(RESPONSE_TO_NONSENSE) - 1)])
            # response = str(chatterbot.get_response(str(userInput)))
            print 'Catterbot response is ' + str(response)
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

def deviseNonsense(taggedInput):
    images = []
    # Before querying the wiki -- perform spell check!
    for word in [word for word in taggedInput if
                 len(word[0]) > 3 and (word[1].startswith('N') or word[1].startswith('J') or word[1].startswith('V'))]:
        correctSpelling = spellCheck(word[0])
        if not correctSpelling == word[0]:
            return SPELLING_ERROR % (correctSpelling, word[0]),[]

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

    queries = [query.replace('your', '').replace('you', '') for query in queries]
    additionalSearchKeywords = [keyword.replace('your', '').replace('you', '') for keyword in additionalSearchKeywords]

    # if addHarryQuery:
    #     queries.append('Harry Potter')

    # Refinement 4. Remove query terms from additionalSearchKeywords to avoid duplication
    for query in queries:
        additionalSearchKeywords = [keyword.replace(query, "") for keyword in additionalSearchKeywords]

    # Refinement 5. Remove empty strings from queries and additionalSearchKeywords
    additionalSearchKeywords = [value for value in additionalSearchKeywords if value != ' ' and value != '']
    queries = [value for value in queries if value != '']
    additionalSearchKeywords = ['is']
    print 'Devise Nonsense'
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

def deviseAnswer(taggedInput):
    images = []
    # Before querying the wiki -- perform spell check!
    for word in [word for word in taggedInput if
                 len(word[0]) > 3 and (word[1].startswith('N') or word[1].startswith('J') or word[1].startswith('V'))]:
        correctSpelling = spellCheck(word[0])
        if not correctSpelling == word[0]:
            return SPELLING_ERROR % (correctSpelling, word[0]),[]

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

    queries = [query.replace('your', '').replace('you', '').replace(' i ', ' ').replace(' me ', ' ') for query in queries]
    additionalSearchKeywords = [keyword.replace('your', '').replace('you', '') for keyword in additionalSearchKeywords]

    # if addHarryQuery:
    #     queries.append('Harry Potter')

    # Refinement 4. Remove query terms from additionalSearchKeywords to avoid duplication
    for query in queries:
        additionalSearchKeywords = [keyword.replace(query, "") for keyword in additionalSearchKeywords]

    # Refinement 5. Remove empty strings from queries and additionalSearchKeywords
    additionalSearchKeywords = [value for value in additionalSearchKeywords if value != ' ' and value != '']
    queries = [value for value in queries if value != '']
    print 'Devise Answer'
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
    correctSpelling = correct(word.upper())
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

        sentences = sent_tokenize(
            resultData['sections'][0]['content'][0]['text'].replace('Â', '').replace('b.', 'born'))
        # Replace any keyword hinting at Hermione with the proper personal pronoun and if followed by 'is' replace with 'am'
        # answer = ' '.join(sentences[0:2]).replace('Harry\'s', 'my').replace('Harry Potter is', 'I am').replace('Harry is', 'I am').replace(
        #     'Harry James Potter', 'I').replace('Harry Potter', 'I').replace('Harry', 'I')
        answer = ' '.join(sentences[0:2])
        answer = answer.replace('Â', '')

        ## Uncomment here
        # if answerWithScore[1] > answerScore:
        #     answerScore = answerWithScore[1]
        #     answer = answerWithScore[0]

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
                answer = answer.replace('Â', '')

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
    counter = 0
    for section in articleData['sections']:
        ## loop through images
        for image in section['images']:
            title = '...'
            if not 'src' in image:
                continue
            src = image['src'].split("/revision/")[0]
            print src
            title = image['caption']
            image_element ={
                "title": title,
                "image_url": src
            }
            images.append(image_element)
            counter +=1
            if counter >5:
                break
        if counter >5:
            break

        ## loop through content
        for content in section['content']:
            ## fetch text and loop through sentences
            if not 'text' in content:
                continue

            for sentence in sent_tokenize(content['text'].replace('b.', 'born').replace('Â', '')):
                sentenceScore = 0

                print str(sentence)
                ## loop through refinements to see if they're in the sentence
                for refinement in searchRefinement:

                    if refinement in sentence:
                        sentenceScore = sentenceScore + 0.5 + (
                        sentence.count(refinement) / len(sentence.rsplit(" ")))

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
    intro = "I can help you know more about the Harry Potter World ,Characters ,Spells and sort you in a house to compete with your friends and see who will win the House Cup at the end of each month."
    FB.send_message(os.environ["PAGE_ACCESS_TOKEN"], user_id, intro)
    FB.send_intro_screenshots(app, os.environ["PAGE_ACCESS_TOKEN"], user_id)

def handle_characters(user_id):
    intro = "You can ask me about any character simply by asking me :D !!\nJust like that \"Who's Harry Potter?\"\n\"Who's pet was Fang?\""
    FB.send_quick_replies_characters(os.environ["PAGE_ACCESS_TOKEN"], user_id, intro)
    # FB.send_intro_screenshots(app, os.environ["PAGE_ACCESS_TOKEN"], user_id)

def handle_spells(user_id):
    intro = "You can ask me about any spell simply by asking me :D !!\nJust like that \"What is Wingardium Leviosa?\"\n\"What is Expecto Patronum?\""
    FB.send_quick_replies_spells(os.environ["PAGE_ACCESS_TOKEN"], user_id, intro)
    # FB.send_intro_screenshots(app, os.environ["PAGE_ACCESS_TOKEN"], user_id)

def handle_places(user_id):
    intro = "You can ask me about any place simply by asking me :D !!\nJust like that \"What is Diagon Alley?\"\n\"What is Godric's Hollow?\""
    FB.send_quick_replies_places(os.environ["PAGE_ACCESS_TOKEN"], user_id, intro)
    # FB.send_intro_screenshots(app, os.environ["PAGE_ACCESS_TOKEN"], user_id)

def handle_first_time_user(db,sender_id,user):
    user_obj = dbAPI.user_exists(db, sender_id)
    user_id = sender_id
    token = os.environ["PAGE_ACCESS_TOKEN"]

    # hi = "%s Wizard, Nice to meet you :)" % (NLP.sayHiTimeZone(user))
    hi = "%s %s, nice to meet you" % (NLP.sayHiTimeZone(user), user['first_name'])
    FB.send_message(token, user_id, hi)

    FB.send_picture(token, user_id, 'https://media.giphy.com/media/12kmDEDUpTWe3e/giphy.gif')

    handle_help(user_id)
    # FB.send_message(token, user_id, "")
    FB.send_quick_replies_help(token, sender_id, 'Next time just tell me \"Help\" to view this again :D')

def handleSortingHat(db,user_id):
    user = dbAPI.user_exists(db,user_id)
    if not user:
        print 'User Added'
        if user.get_q1() == None:
            send_q1(user_id)
        elif user.get_q2() == None:
            send_q2(user_id)
        elif user.get_q3() == None:
            send_q3(user_id)
        elif user.get_q4() == None:
            send_q4(user_id)
        elif user.get_q5() == None:
            send_q5(user_id)
    else:
        if user.get_q1() == None:
            FB.send_picture(token, user_id, 'http://geekgirlcon.com/wp-content/uploads/2015/07/tumblr_lo74ldL68x1ql0adio1_500.gif')
            FB.send_message(token, user_id, 'Hmm, difficult. VERY difficult. I wonder where to put you?')
            send_q1(user_id)
        elif user.get_q2() == None:
            send_q2(user_id)
        elif user.get_q3() == None:
            send_q3(user_id)
        elif user.get_q4() == None:
            send_q4(user_id)
        elif user.get_q5() == None:
            send_q5(user_id)
        else:
            sortHatResult(user_id)

        print 'User Exists'

def sortHatResult(user_id):
    user = dbAPI.user_exists(db, user_id)
    house = user.get_house()
    print 'house is '+ str(user.house)
    if house == 'Hufflepuff':
        house = House.query.filter_by(name='Hufflepuff').first()

        sendHouseResult(user_id,'Yaaay!! I have been sorted into Hufflepuff.','You should try yourself and see which house you will be sorted into','Congratulations!! You have been sorted into Hufflepuff','You might belong in Hufflepuff,Where they are just and loyal,Those patient Hufflepuffs are true,And unafraid of toil','https://images.pottermore.com/bxd3o8b291gf/2GyJvxXe40kkkG0suuqUkw/e1a64ec404cf5f19afe9053b9d375230/PM_House_Pages_400_x_400_px_FINAL_CREST3.png?w=550&h=550&fit=thumb&f=center&q=85')
    elif house == 'Ravenclaw':
        house = House.query.filter_by(name='Ravenclaw').first()
        sendHouseResult(user_id,'Yaaay!! I have been sorted into Ravenclaw.','You should try yourself and see which house you will be sorted into', 'Congratulations!! You have been sorted into Ravenclaw',
                        'Or yet in wise old Ravenclaw,If you\'ve a ready mind,Where those of wit and learning,Will always find their kind.',
                        'https://images.pottermore.com/bxd3o8b291gf/5pnnQ5puTuywEEW06w2gSg/91abff3d923b4785ed79e9abda07bd07/PM_House_Pages_400_x_400_px_FINAL_CREST.png?w=550&h=550&fit=thumb&f=center&q=85')
    elif house == 'Gryffindor':
        house = House.query.filter_by(name='Gryffindor').first()
        sendHouseResult(user_id,'Yaaay!! I have been sorted into Gryffindor.','You should try yourself and see which house you will be sorted into', 'Congratulations!! You have been sorted into Gryffindor',
                        'You might belong in Gryffindor,Where dwell the brave at heart,Their daring, nerve, and chivalrySet Gryffindors apart',
                        'https://images.pottermore.com/bxd3o8b291gf/49zkCzoZlekCmSq6OsycAm/da6278c1af372f18f8b6a71b226e0814/PM_House_Pages_400_x_400_px_FINAL_CREST2.png?w=550&h=550&fit=thumb&f=center&q=85')
    elif house == 'Slytherin':
        house = House.query.filter_by(name='Slytherin').first()
        sendHouseResult(user_id,'Yaaay!! I have been sorted into Slytherin.','You should try yourself and see which house you will be sorted into', 'Congratulations!! You have been sorted into Slytherin',
                        'Or perhaps in Slytherin,You\'ll make your real friends,Those cunning folk use any means,To achieve their ends.',
                        'https://images.pottermore.com/bxd3o8b291gf/4U98maPA5aEUWcO8uOisOq/e01e17cc414b960380acbf8ace1dc1d5/PM_House_Pages_400_x_400_px_FINAL_CREST4.png?w=550&h=550&fit=thumb&f=center&q=85')
    GreateHallReplies(user_id)

def sendHouseResult(user_id,title_share,subtitle_share,title,subtitle,url):
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": os.environ["PAGE_ACCESS_TOKEN"]},
                      data=json.dumps({
                          "recipient": {"id": user_id},
                          "message": {
                              "attachment": {
                                  "type": "template",
                                  "payload": {
                                      "template_type": "generic",
                                      "sharable": True,
                                      "elements": [{
                                          "title": title,
                                          "subtitle": subtitle,
                                          "image_url": url,
                                          "buttons":[
                                                {
                                                    "type": "postback",
                                                    "title": "View House",
                                                    "payload": "Harry_Botter_House"
                                                },{
                                                  "type": "element_share",
                                                  "share_contents": {
                                                      "attachment": {
                                                          "type": "template",
                                                          "payload": {
                                                              "template_type": "generic",
                                                              "sharable": True,
                                                              "elements": [{
                                                                  "title": title_share,
                                                                  "subtitle": subtitle_share,
                                                                  "image_url": url,
                                                                  "buttons":[
                                                                        {
                                                                            "type": "web_url",
                                                                            "title": "Try It!!",
                                                                            "url": "https://www.messenger.com/t/harrybottermessenger?ref=Harry_Botter_Add_Share_Points,"+str(user_id)
                                                                        }
                                                                    ]
                            }
                                                              ]
                                                  }}}
                                              }
                                            ]
    }
                                      ]
                                  }
                              }
                          }
                      }),
                      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print r.text

def handleViewHouse(db,user_id):
    user = dbAPI.user_exists(db,user_id)
    if not user.house:
        handleSortingHat(db,user_id)
    else:

        house = user.get_house()

        houses = User.query.all()
        if not house:
            handleSortingHat(db,user_id)
            return 'OK'
        elif house == 'Hufflepuff':
            house_obj = House.query.filter_by(name=house).first()
            house_name = 'House Hufflepuff'
            house_traits = 'Dedication,Hard Work,Fair play,Patience,Kindness'
            house_founder = 'Helga Hufflepuff'
            house_founder_url = 'https://vignette3.wikia.nocookie.net/harrypotter/images/8/8c/PR_007_001-e1313269883743.jpg/revision/latest?cb=20140615154415'
            num = 0
            points = 0
            for house_n in houses:
                if house_n.house == 'Hufflepuff':
                    num += 1
                    points += house_n.points

            house_points = points
            house_members_number = num
            house_url = 'https://images.pottermore.com/bxd3o8b291gf/2GyJvxXe40kkkG0suuqUkw/e1a64ec404cf5f19afe9053b9d375230/PM_House_Pages_400_x_400_px_FINAL_CREST3.png?w=550&h=550&fit=thumb&f=center&q=85'
        elif house == 'Ravenclaw':
            house_obj = House.query.filter_by(name=house).first()
            house_name = 'House Ravenclaw'
            house_traits = 'Intelligence,Wit,Wisdom,Creativity,Originality'
            house_founder = 'Rowena Ravenclaw'
            house_founder_url = 'https://vignette1.wikia.nocookie.net/harrypotter/images/4/4a/PR_007_007-e1313269741697.jpg/revision/latest?cb=20140615151812'
            num = 0
            points = 0
            for house_n in houses:
                if house_n.house == 'Ravenclaw':
                    num += 1
                    points += house_n.points

            house_points = points
            house_members_number = num
            house_url = 'https://images.pottermore.com/bxd3o8b291gf/5pnnQ5puTuywEEW06w2gSg/91abff3d923b4785ed79e9abda07bd07/PM_House_Pages_400_x_400_px_FINAL_CREST.png?w=550&h=550&fit=thumb&f=center&q=85'
        elif house == 'Gryffindor':
            house_obj = House.query.filter_by(name=house).first()
            house_name = 'House Gryffindor'
            house_traits = 'Bravery,Nerve,Chivalry,Courage,Daring'
            house_founder = 'Godric Gryffindor'
            house_founder_url = 'https://vignette2.wikia.nocookie.net/harrypotter/images/3/38/PR_007_003-e1313269822422.jpg/revision/latest?cb=20140615154246'
            num = 0
            points = 0
            for house_n in houses:
                if house_n.house == 'Gryffindor':
                    num += 1
                    points += house_n.points

            house_points = points
            house_members_number = num
            house_url = 'https://images.pottermore.com/bxd3o8b291gf/49zkCzoZlekCmSq6OsycAm/da6278c1af372f18f8b6a71b226e0814/PM_House_Pages_400_x_400_px_FINAL_CREST2.png?w=550&h=550&fit=thumb&f=center&q=85'
        elif house == 'Slytherin':
            house_obj = House.query.filter_by(name=house).first()
            house_name = 'House Slytherin'
            house_traits = 'Resourcefulness,Cunning,Ambition,Determination,Self-Preservation'
            house_founder = 'Salazar Slytherin'
            house_founder_url = 'https://vignette3.wikia.nocookie.net/harrypotter/images/2/2b/PR_007_005-e1313269785740.jpg/revision/latest?cb=20140615154545'

            num = 0
            points = 0
            for house_n in houses:
                if house_n.house == 'Slytherin':
                    num += 1
                    points += house_n.points

            house_points = points
            house_members_number = num
            house_url = 'https://images.pottermore.com/bxd3o8b291gf/4U98maPA5aEUWcO8uOisOq/e01e17cc414b960380acbf8ace1dc1d5/PM_House_Pages_400_x_400_px_FINAL_CREST4.png?w=550&h=550&fit=thumb&f=center&q=85'
        r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                          params={"access_token": os.environ["PAGE_ACCESS_TOKEN"]},
                          data=json.dumps({
                              "recipient": {"id": user_id},
                              "message": {
                                  "attachment": {
                                      "type": "template",
                                      "payload": {
                                            "template_type": "list",
                                            "elements": [
                                                {
                                                    "title": house_name,
                                                    "image_url": house_url,
                                                    "subtitle":str(house_traits),

                                                },
                                                {
                                                    "title": 'House Founder',
                                                    "image_url": house_founder_url,
                                                    "subtitle":'\n' +  str(house_founder),
                                                },
                                                {
                                                    "title": 'House Members Number',
                                                    "subtitle":'\n' +  str(house_members_number),
                                                    "image_url": 'http://www.wetpaint.com/wp-content/uploads/2016/04/harry-potter-cast-then-and-now.jpg',

                                                },
                                                {
                                                    "title": 'House Overall Points',
                                                    "subtitle":'\n' +  str(house_points),
                                                    "image_url": 'http://2.bp.blogspot.com/-mHWyCRTthHY/VeDQ6kDRnsI/AAAAAAAAXZ4/WmIvI9ANNL0/s1600/HP3.jpg',
                                                }
                                            ]
                                      }
                                  }
                              }
                          }),
                          headers={'Content-type': 'application/json'})
        if r.status_code != requests.codes.ok:
            print r.text
        GreateHallReplies(user_id)

def send_q1(user_id):
    Q1 = [ {"What would you least like to be called?":
                 [ {"Ignorant" : "Q1_R"},
                   {"Cowardly" : "Q1_G"},
                   {"Selfish": "Q1_H"},
                   {"Ordinary": "Q1_S"}
                 ]
            },
            {"What title do you want after you're dead?":
                 [ {"The Good": "Q1_H"},
                   {"The Great": "Q1_S"},
                   {"The Wise": "Q1_R"},
                   {"The Bold": "Q1_G"}
                 ]
            },
            { "Brew a potion for one quality, which is it?":
                 [ {"Love": "Q1_H"},
                   {"Glory": "Q1_G"},
                   {"Wisdom": "Q1_R"},
                   {"Power": "Q1_S"}
                 ]
            }
          ]
    question = NLP.oneOf(Q1)
    title = question.keys()[0]
    answers = question.get(title)
    buttons =[]
    for answer in answers:
        key = answer.keys()[0]
        value = answer.values()[0]
        button = {
            "content_type": "text",
            "title": key,
            "payload": value
        }
        buttons.append(button)

    data = {
        "recipient": {"id": user_id},
        "message": {
            "text": title,
            "quick_replies": buttons
        }
    }
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": os.environ["PAGE_ACCESS_TOKEN"]},
                      data=json.dumps(data),
                      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print r.text

def send_q2(user_id):
    Q2 = [ { "Which instrument is most pleasing to your ear?":
                  [ {"Piano": "Q2_R"},
                    {"Violin": "Q2_S"},
                    {"Trumpet": "Q2_H"},
                    {"Drums": "Q2_G" }
                  ]
            },
            { "What smell is most appealing to you?":
                  [ {"Home": "Q2_H"},
                    {"The sea": "Q2_S" },
                    {"Fresh Parchment": "Q2_R"},
                    {"A log fire": "Q2_G" }
                  ]
            }
            ]
    question = NLP.oneOf(Q2)
    title = question.keys()[0]
    answers = question.get(title)
    buttons = []
    for answer in answers:
        key = answer.keys()[0]
        value = answer.values()[0]
        button = {
            "content_type": "text",
            "title": key,
            "payload": value
        }
        buttons.append(button)

    data = {
        "recipient": {"id": user_id},
        "message": {
            "text": title,
            "quick_replies": buttons
        }
    }
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": os.environ["PAGE_ACCESS_TOKEN"]},
                      data=json.dumps(data),
                      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print r.text

def send_q3(user_id):
    Q3 = [ {"A troll breaks into the Headmaster's study. Order the following items in the order you would save them":
                  [ {"Cure >Book > Records": "Q3_G"},
                    {"Cure >Records > Book": "Q3_H"},
                    {"Book >Cure > Records": "Q3_R"},
                    {"Book >Records > Cure": "Q3_S"},
                    {"Records >Cure > Book": "Q3_H"},
                    {"Records >Book > Cure": "Q3_S"}
                  ]
             },
            {"What would you rather be?":
                  [ {"Trusted": "Q3_H"},
                    {"Liked": "Q3_H" },
                    {"Praised": "Q3_G" },
                    {"Feared": "Q3_R" },
                    {"Envied": "Q3_S" },
                    {"Imitated": "Q3_S" }
                  ]
            },
            {"Which of the following do you have the most trouble dealing with?":
                  [ {"Hunger": "Q3_H"},
                    {"Cold": "Q3_S"},
                    {"Being Ignored": "Q3_S"},
                    {"Boredom": "Q3_G"},
                    {"Loneliness": "Q3_H"}
                  ]
            }
           ]
    question = NLP.oneOf(Q3)
    title = question.keys()[0]
    answers = question.get(title)
    buttons = []
    for answer in answers:
        key = answer.keys()[0]
        value = answer.values()[0]
        button = {
            "content_type": "text",
            "title": key,
            "payload": value
        }
        buttons.append(button)

    data = {
        "recipient": {"id": user_id},
        "message": {
            "text": title,
            "quick_replies": buttons
        }
    }
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": os.environ["PAGE_ACCESS_TOKEN"]},
                      data=json.dumps(data),
                      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print r.text

def send_q4(user_id):
    Q4 = [ {"If you could have a superpower, which would you choose?":
                  [ {"Read Minds": "Q4_R" },
                    {"Invisibility": "Q4_G" },
                    {"Change the past": "Q4_S" },
                    {"Change your appearance": "Q4_S" },
                    {"Talk to animals": "Q4_H"},
                    {"Superstrength": "Q4_H" }
                  ]
            },
            {"Which of the following would you most like to study?":
                  [ {"Centaurs": "Q4_R" },
                    {"Merpeople": "Q4_S" },
                    {"Ghosts": "Q4_G" },
                    {"Werewolves": "Q4_H" },
                    {"Vampires": "Q4_S" },
                    {"Goblins": "Q4_S" },
                    {"Trolls": "Q4_H" }
                  ]
            },
            {"Which subject at Hogwarts would you be most interested in studying?":
                  [ {"STUDY ALL THE THINGS!": "Q4_R" },
                    {"Apparition": "Q4_S" },
                    {"Hexes/Jinxes": "Q4_S" },
                    {"Secrets about castle": "Q4_G" },
                    {"Transfiguration": "Q4_R" },
                    {"Broom Flying": "Q4_G" },
                    {"Magical Creatures": "Q4_H" }
                  ]
            },
          ]
    question = NLP.oneOf(Q4)
    title = question.keys()[0]
    answers = question.get(title)
    buttons = []
    for answer in answers:
        key = answer.keys()[0]
        value = answer.values()[0]
        button = {
            "content_type": "text",
            "title": key,
            "payload": value
        }
        buttons.append(button)

    data = {
        "recipient": {"id": user_id},
        "message": {
            "text": title,
            "quick_replies": buttons
        }
    }
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": os.environ["PAGE_ACCESS_TOKEN"]},
                      data=json.dumps(data),
                      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print r.text

def send_q5(user_id):
    Q5 = [ {"You and your friends need to cross a bridge guarded by a river troll. He insists that one of you fight him before you can cross. What do you do?":
                 [ {"Confuse the troll": "Q5_R" },
                   {"Have all 3 to fight": "Q5_S" },
                   {"Volunteer to fight": "Q5_G" },
                   {"Draw lots to see who fights": "Q5_H" }
                 ]
             },
            {"Which path do you take?":
                 [ {"Leafy path in woods": "Q5_G" },
                   {"A dark, little alley": "Q5_S" },
                   {"A sunny, grassy path": "Q5_H" },
                   {"A cobblestone street lined with ancient buildings": "Q5_R" }
                 ]
            },
            {"A Muggle approaches you and says you're a wizard. How do you react?":
                 [ {"Ask why they think so": "Q5_R" },
                   {"Agree and offer a sample of a jinx": "Q5_S" },
                   {"Agree and walk away, bluffing": "Q5_G" },
                   {"Offer to call hospital": "Q5_H" }
                 ]
            }
            ]
    question = NLP.oneOf(Q5)
    title = question.keys()[0]
    answers = question.get(title)
    buttons = []
    for answer in answers:
        key = answer.keys()[0]
        value = answer.values()[0]
        button = {
            "content_type": "text",
            "title": key,
            "payload": value
        }
        buttons.append(button)

    data = {
        "recipient": {"id": user_id},
        "message": {
            "text": title,
            "quick_replies": buttons
        }
    }
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": os.environ["PAGE_ACCESS_TOKEN"]},
                      data=json.dumps(data),
                      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print r.text

def SortingResult(db,user_id):
    G = 0
    S = 0
    R = 0
    H = 0
    user = dbAPI.user_exists(db, user_id)
    q1 = user.get_q1()
    if q1 == 'G':
        G +=1
    elif q1 == 'S':
        S +=1
    elif q1 == 'R':
        R +=1
    elif q1 == 'H':
        H +=1
    q2 = user.get_q2()
    if q2 == 'G':
        G +=1
    elif q2 == 'S':
        S +=1
    elif q2 == 'R':
        R +=1
    elif q2 == 'H':
        H +=1
    q3 = user.get_q3()
    if q3 == 'G':
        G +=1
    elif q3 == 'S':
        S +=1
    elif q3 == 'R':
        R +=1
    elif q3 == 'H':
        H +=1
    q4 = user.get_q4()
    if q4 == 'G':
        G +=1
    elif q4 == 'S':
        S +=1
    elif q4 == 'R':
        R +=1
    elif q4 == 'H':
        H +=1
    q5 = user.get_q5()
    if q5 == 'G':
        G +=1
    elif q5 == 'S':
        S +=1
    elif q5 == 'R':
        R +=1
    elif q5 == 'H':
        H +=1

    AllHouses = [H, R, G, S]
    House_dict = {H: "Hufflepuff", R: "Ravenclaw", G: "Gryffindor", S: "Slytherin"}
    Dominant_House = max(AllHouses)
    for house in House_dict:
        if house == Dominant_House:
            house_obj = House.query.filter_by(name=House_dict[house]).first()
            num = house_obj.members_num
            print 'Numbeeeeeer is ' + str(num)
            house_obj.members_num = num + 1
            print 'Numbeeeeeer again is ' + str(house_obj.members_num)
            db.session.commit()
            user.house = House_dict[house]
            db.session.commit()
    sortHatResult(user_id)

def handleTrivia(db,user_id):
    user = dbAPI.user_exists(db,user_id)
    if not user.house:
        handleSortingHat(db,user_id)
    else:

        question = NLP.oneOf(QBank)
        title = question.keys()[0]
        answers = question.get(title)
        buttons = []
        for answer in answers:
            key = answer.keys()[0]
            value = answer.values()[0]
            button = {
                "content_type": "text",
                "title": key,
                "payload": value
            }
            buttons.append(button)

        data = {
            "recipient": {"id": user_id},
            "message": {
                "text": title,
                "quick_replies": buttons
            }
        }
        r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                          params={"access_token": os.environ["PAGE_ACCESS_TOKEN"]},
                          data=json.dumps(data),
                          headers={'Content-type': 'application/json'})
        if r.status_code != requests.codes.ok:
            print r.text

def handleWrongAnswer(db,user_id):
    images = ['wrong1.jpg','wrong2.gif','wrong3.jpg','wrong4.jpg','wrong5.gif']
    image = NLP.oneOf(images)
    FB.send_picture(token, user_id, url_for('static', filename="assets/img/"+ str(image), _external=True))
    data = {
        "recipient": {"id": user_id},
        "message": {
            "text": 'Wrong Answer!!',
            "quick_replies": [
                {
                    "content_type": "text",
                    "title": 'Another Question',
                    "payload": 'Harry_Botter_Trivia_Question'
                },
                {
                    "content_type": "text",
                    "title": 'My House',
                    "payload": 'Harry_Botter_House'
                },
                {
                    "content_type": "text",
                    "title": 'My Profile',
                    "payload": 'Harry_Botter_Profile'
                },
                {
                    "content_type": "text",
                    "title": 'All Houses',
                    "payload": 'Harry_Botter_Houses'
                },
                {
                    "content_type": "text",
                    "title": 'Leaderboard',
                    "payload": 'Harry_Botter_LeaderBoard'
                },
            ]
        }
    }
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": os.environ["PAGE_ACCESS_TOKEN"]},
                      data=json.dumps(data),
                      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print r.text

def handleCorrectAnswer(db,user_id):
    images = ['correct1.gif', 'correct2.jpg', 'correct3.gif', 'correct4.gif', 'correct5.gif']
    image = NLP.oneOf(images)
    FB.send_picture(token, user_id, url_for('static', filename="assets/img/" + str(image), _external=True))
    user = dbAPI.user_exists(db, user_id)
    house = user.house
    house_obj = House.query.filter_by(name=house).first()
    send_message(user_id,'Correct Answer!!')
    # send_message(user_id, '10 Point to '+ str(house))
    print 'Points isssss ' + str(user.points)
    user_points = user.points
    house_points = house_obj.points
    user_points += 10
    house_points += 10
    # user.update_score(points)
    # house_obj.update_score(points)
    user.points = user_points
    house_obj.points = house_points
    db.session.commit()
    data = {
        "recipient": {"id": user_id},
        "message": {
            "text": '10 Point to '+ str(house),
            "quick_replies": [
                {
                    "content_type": "text",
                    "title": 'Another Question',
                    "payload": 'Harry_Botter_Trivia_Question'
                },
                {
                    "content_type": "text",
                    "title": 'My House',
                    "payload": 'Harry_Botter_House'
                },
                {
                    "content_type": "text",
                    "title": 'My Profile',
                    "payload": 'Harry_Botter_Profile'
                },
                {
                    "content_type": "text",
                    "title": 'All Houses',
                    "payload": 'Harry_Botter_Houses'
                },
                {
                    "content_type": "text",
                    "title": 'Leaderboard',
                    "payload": 'Harry_Botter_LeaderBoard'
                },
            ]
        }
    }
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": os.environ["PAGE_ACCESS_TOKEN"]},
                      data=json.dumps(data),
                      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print r.text

def handleProfile(db,user_id):
    user = dbAPI.user_exists(db,user_id)
    if not user.house:
        handleSortingHat(db,user_id)
    else:

        house = user.house
        points = user.points
        if house == 'Hufflepuff':
            house_url = 'https://images.pottermore.com/bxd3o8b291gf/2GyJvxXe40kkkG0suuqUkw/e1a64ec404cf5f19afe9053b9d375230/PM_House_Pages_400_x_400_px_FINAL_CREST3.png?w=550&h=550&fit=thumb&f=center&q=85'
        elif house == 'Ravenclaw':
            house_url = 'https://images.pottermore.com/bxd3o8b291gf/5pnnQ5puTuywEEW06w2gSg/91abff3d923b4785ed79e9abda07bd07/PM_House_Pages_400_x_400_px_FINAL_CREST.png?w=550&h=550&fit=thumb&f=center&q=85'
        elif house == 'Gryffindor':
            house_url = 'https://images.pottermore.com/bxd3o8b291gf/49zkCzoZlekCmSq6OsycAm/da6278c1af372f18f8b6a71b226e0814/PM_House_Pages_400_x_400_px_FINAL_CREST2.png?w=550&h=550&fit=thumb&f=center&q=85'
        elif house == 'Slytherin':
            house_url = 'https://images.pottermore.com/bxd3o8b291gf/4U98maPA5aEUWcO8uOisOq/e01e17cc414b960380acbf8ace1dc1d5/PM_House_Pages_400_x_400_px_FINAL_CREST4.png?w=550&h=550&fit=thumb&f=center&q=85'
        FBUser = FB.get_user_fb(token,user_id)
        profile_pic = FBUser['profile_pic']
        first_name = FBUser['first_name']
        last_name = FBUser['last_name']
        r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                          params={"access_token": os.environ["PAGE_ACCESS_TOKEN"]},
                          data=json.dumps({
                              "recipient": {"id": user_id},
                              "message": {
                                  "attachment": {
                                      "type": "template",
                                      "payload": {
                                          "template_type": "list",
                                          "elements": [
                                              {
                                                  "title": 'Name',
                                                  "image_url": profile_pic,
                                                  "subtitle":str(first_name) + ' '+ str(last_name),

                                              },
                                              {
                                                  "title": 'House Name',
                                                  "image_url": house_url,
                                                  "subtitle": '\n' + str(house),
                                                  "buttons": [
                                                      {
                                                          "title": "View House",
                                                          "type": "postback",
                                                          "payload": "Harry_Botter_House" ,
                                                      }

                                                  ]
                                              },
                                              {
                                                  "title": 'Points',
                                                  "subtitle": '\n' + str(points),
                                                  "image_url": 'http://2.bp.blogspot.com/-mHWyCRTthHY/VeDQ6kDRnsI/AAAAAAAAXZ4/WmIvI9ANNL0/s1600/HP3.jpg',
                                              }
                                          ]
                                      }
                                  }
                              }
                          }),
                          headers={'Content-type': 'application/json'})
        if r.status_code != requests.codes.ok:
            print r.text
        GreateHallReplies(user_id)

def handleViewHouses(db, user_id):
    user = dbAPI.user_exists(db, user_id)
    if not user.house:
        handleSortingHat(db,user_id)
    else:
        houses = User.query.all()
        house = user.get_house()
        num_h = 0
        points_h = 0
        num_r = 0
        points_r = 0
        num_g = 0
        points_g = 0
        num_s = 0
        points_s = 0
        for house_n in houses:
            if house_n.house == 'Slytherin':
                num_s += 1
                points_s += house_n.points

            elif house_n.house == 'Hufflepuff':
                num_h += 1
                points_h += house_n.points

            elif house_n.house == 'Ravenclaw':
                num_r += 1
                points_r += house_n.points

            elif house_n.house == 'Gryffindor':
                num_g += 1
                points_g += house_n.points


        house_points_s = points_s
        house_members_number_s = num_s
        house_points_r = points_r
        house_members_number_r = num_r
        house_points_h = points_h
        house_members_number_h = num_h
        house_points_g = points_g
        house_members_number_g = num_g


        if house == 'Hufflepuff':
            house1_url = 'https://images.pottermore.com/bxd3o8b291gf/2GyJvxXe40kkkG0suuqUkw/e1a64ec404cf5f19afe9053b9d375230/PM_House_Pages_400_x_400_px_FINAL_CREST3.png?w=550&h=550&fit=thumb&f=center&q=85'
            title1 = 'Hufflepuff'
            subtitle1 = 'Members: '+ str(house_members_number_h) + ' | Points: '+ str(house_points_h)
            house2_url = 'https://images.pottermore.com/bxd3o8b291gf/5pnnQ5puTuywEEW06w2gSg/91abff3d923b4785ed79e9abda07bd07/PM_House_Pages_400_x_400_px_FINAL_CREST.png?w=550&h=550&fit=thumb&f=center&q=85'
            title2 = 'Ravenclaw'
            subtitle2 = 'Members: ' + str(house_members_number_r) + '\n\nPoints: ' + str(house_points_r)
            house3_url = 'https://images.pottermore.com/bxd3o8b291gf/49zkCzoZlekCmSq6OsycAm/da6278c1af372f18f8b6a71b226e0814/PM_House_Pages_400_x_400_px_FINAL_CREST2.png?w=550&h=550&fit=thumb&f=center&q=85'
            title3 = 'Gryffindor'
            subtitle3 = 'Members: ' + str(house_members_number_g) + '\n\nPoints: ' + str(house_points_g)
            house4_url = 'https://images.pottermore.com/bxd3o8b291gf/4U98maPA5aEUWcO8uOisOq/e01e17cc414b960380acbf8ace1dc1d5/PM_House_Pages_400_x_400_px_FINAL_CREST4.png?w=550&h=550&fit=thumb&f=center&q=85'
            title4 = 'Slytherin'
            subtitle4 = 'Members: ' + str(house_members_number_s) + '\n\nPoints: ' + str(house_points_s)
        elif house == 'Ravenclaw':
            house2_url = 'https://images.pottermore.com/bxd3o8b291gf/2GyJvxXe40kkkG0suuqUkw/e1a64ec404cf5f19afe9053b9d375230/PM_House_Pages_400_x_400_px_FINAL_CREST3.png?w=550&h=550&fit=thumb&f=center&q=85'
            title2 = 'Hufflepuff'
            subtitle2 = 'Members: ' + str(house_members_number_h) + '\n\nPoints: ' + str(house_points_h)
            house1_url = 'https://images.pottermore.com/bxd3o8b291gf/5pnnQ5puTuywEEW06w2gSg/91abff3d923b4785ed79e9abda07bd07/PM_House_Pages_400_x_400_px_FINAL_CREST.png?w=550&h=550&fit=thumb&f=center&q=85'
            title1 = 'Ravenclaw'
            subtitle1 = 'Members: ' + str(house_members_number_r) + ' | Points: ' + str(house_points_r)
            house3_url = 'https://images.pottermore.com/bxd3o8b291gf/49zkCzoZlekCmSq6OsycAm/da6278c1af372f18f8b6a71b226e0814/PM_House_Pages_400_x_400_px_FINAL_CREST2.png?w=550&h=550&fit=thumb&f=center&q=85'
            title3 = 'Gryffindor'
            subtitle3 = 'Members: ' + str(house_members_number_g) + '\n\nPoints: ' + str(house_points_g)
            house4_url = 'https://images.pottermore.com/bxd3o8b291gf/4U98maPA5aEUWcO8uOisOq/e01e17cc414b960380acbf8ace1dc1d5/PM_House_Pages_400_x_400_px_FINAL_CREST4.png?w=550&h=550&fit=thumb&f=center&q=85'
            title4 = 'Slytherin'
            subtitle4 = 'Members: ' + str(house_members_number_s) + '\n\nPoints: ' + str(house_points_s)
        elif house == 'Gryffindor':
            house3_url = 'https://images.pottermore.com/bxd3o8b291gf/2GyJvxXe40kkkG0suuqUkw/e1a64ec404cf5f19afe9053b9d375230/PM_House_Pages_400_x_400_px_FINAL_CREST3.png?w=550&h=550&fit=thumb&f=center&q=85'
            title3 = 'Hufflepuff'
            subtitle3 = 'Members: ' + str(house_members_number_h) + '\n\nPoints: ' + str(house_points_h)
            house2_url = 'https://images.pottermore.com/bxd3o8b291gf/5pnnQ5puTuywEEW06w2gSg/91abff3d923b4785ed79e9abda07bd07/PM_House_Pages_400_x_400_px_FINAL_CREST.png?w=550&h=550&fit=thumb&f=center&q=85'
            title2 = 'Ravenclaw'
            subtitle2 = 'Members: ' + str(house_members_number_r) + '\n\nPoints: ' + str(house_points_r)
            house1_url = 'https://images.pottermore.com/bxd3o8b291gf/49zkCzoZlekCmSq6OsycAm/da6278c1af372f18f8b6a71b226e0814/PM_House_Pages_400_x_400_px_FINAL_CREST2.png?w=550&h=550&fit=thumb&f=center&q=85'
            title1 = 'Gryffindor'
            subtitle1 = 'Members: ' + str(house_members_number_g) + ' | Points: ' + str(house_points_g)
            house4_url = 'https://images.pottermore.com/bxd3o8b291gf/4U98maPA5aEUWcO8uOisOq/e01e17cc414b960380acbf8ace1dc1d5/PM_House_Pages_400_x_400_px_FINAL_CREST4.png?w=550&h=550&fit=thumb&f=center&q=85'
            title4 = 'Slytherin'
            subtitle4 = 'Members: ' + str(house_members_number_s) + '\n\nPoints: ' + str(house_points_s)
        elif house == 'Slytherin':
            house4_url = 'https://images.pottermore.com/bxd3o8b291gf/2GyJvxXe40kkkG0suuqUkw/e1a64ec404cf5f19afe9053b9d375230/PM_House_Pages_400_x_400_px_FINAL_CREST3.png?w=550&h=550&fit=thumb&f=center&q=85'
            title4 = 'Hufflepuff'
            subtitle4 = 'Members: ' + str(house_members_number_h) + '\n\nPoints: ' + str(house_points_h)
            house2_url = 'https://images.pottermore.com/bxd3o8b291gf/5pnnQ5puTuywEEW06w2gSg/91abff3d923b4785ed79e9abda07bd07/PM_House_Pages_400_x_400_px_FINAL_CREST.png?w=550&h=550&fit=thumb&f=center&q=85'
            title2 = 'Ravenclaw'
            subtitle2 = 'Members: ' + str(house_members_number_r) + '\n\nPoints: ' + str(house_points_r)
            house3_url = 'https://images.pottermore.com/bxd3o8b291gf/49zkCzoZlekCmSq6OsycAm/da6278c1af372f18f8b6a71b226e0814/PM_House_Pages_400_x_400_px_FINAL_CREST2.png?w=550&h=550&fit=thumb&f=center&q=85'
            title3 = 'Gryffindor'
            subtitle3 = 'Members: ' + str(house_members_number_g) + '\n\nPoints: ' + str(house_points_g)
            house1_url = 'https://images.pottermore.com/bxd3o8b291gf/4U98maPA5aEUWcO8uOisOq/e01e17cc414b960380acbf8ace1dc1d5/PM_House_Pages_400_x_400_px_FINAL_CREST4.png?w=550&h=550&fit=thumb&f=center&q=85'
            title1 = 'Slytherin'
            subtitle1 = 'Members: ' + str(house_members_number_s) + ' | Points: ' + str(house_points_s)

        r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                          params={"access_token": os.environ["PAGE_ACCESS_TOKEN"]},
                          data=json.dumps({
                              "recipient": {"id": user_id},
                              "message": {
                                  "attachment": {
                                      "type": "template",
                                      "payload": {
                                          "template_type": "list",
                                          "elements": [
                                              {
                                                  "title": title1,
                                                  "image_url": house1_url,
                                                  "subtitle":str(subtitle1),

                                              },
                                              {
                                                  "title": title2,
                                                  "image_url": house2_url,
                                                  "subtitle": '\n' + str(subtitle2),

                                              },
                                              {
                                                  "title": title3,
                                                  "image_url": house3_url,
                                                  "subtitle": '\n' + str(subtitle3),

                                              },
                                              {
                                                  "title": title4,
                                                  "image_url": house4_url,
                                                  "subtitle": '\n' + str(subtitle4),

                                              }
                                          ]
                                      }
                                  }
                              }
                          }),
                          headers={'Content-type': 'application/json'})
        if r.status_code != requests.codes.ok:
            print r.text
        GreateHallReplies(user_id)

def handleShare(db,user_id,sender_id):
    shared = False
    # print ' Wooowzzaaaaaa'
    user = dbAPI.user_exists(db, user_id)
    if not user.house:
        handleSortingHat(db,user_id)
    else:
        # sender = dbAPI.user_exists(db, user_id)
        user_sharings = Shared_with.query.all()
        for sharing in user_sharings:
            if sharing.shared_with_id == sender_id:
                print 'Shared With before'
                shared = True
                break
        if shared == False:
            print 'Not Shared With before'
            share = Shared_with(user_id,sender_id)
            db.session.add(share)
            house = user.house
            house_obj = House.query.filter_by(name=house).first()
            send_message(user_id, 'You have Shared Harry Botter Successfully with a friend.')
            send_message(user_id, '10 Point to ' + str(house))
            # print 'Points isssss ' + str(user.points)
            user_points = user.points
            house_points = house_obj.points
            user_points += 10
            house_points += 10
            # user.update_score(points)
            # house_obj.update_score(points)
            user.points = user_points
            house_obj.points = house_points
            db.session.commit()

def handleLeaderBoard(db,user_id):
    users = User.query.all()
    first = 0
    fpoints = 0
    second = 0
    spoints = 0
    third = 0
    tpoints = 0
    for user in users:
        # print str(user.points)
        if user.points > fpoints:
            # print ' Oneeeee'
            if second != 0:
                third = second
                tpoints = third.points
            if first != 0:
                second = first
                spoints = second.points

            first = user
            fpoints = first.points


        elif user.points > spoints:
            # print 'Twooooooo'
            if second != 0:
                third = second
                tpoints = third.points
            second = user
            spoints = second.points

        elif user.points > tpoints:
            # print ' Threeeeeeeeee'
            third = user
            tpoints = third.points

    if fpoints==0:
        first = users[0]
        second = users[1]
        third = users[2]

    elif spoints==0:
        second = users[0]
        third = users[1]

    elif tpoints==0:
        third = users[0]

    FBUser1 = FB.get_user_fb(token, first.user_id)
    FBUser2 = FB.get_user_fb(token, second.user_id)
    FBUser3 = FB.get_user_fb(token, third.user_id)
    print second.house
    print second.points
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=json.dumps({
                          "recipient": {"id": user_id},
                          "message": {
                              "attachment": {
                                  "type": "template",
                                  "payload": {
                                      "template_type": "generic",
                                      "elements": [
                                          {
                                              "title": str(FBUser1['first_name']) + ' '+ str(FBUser1['last_name']),
                                              "image_url": FBUser1['profile_pic'],
                                              "subtitle":str(first.house)+'\n'+'Points : '+ str(first.points)
                                          },
                                          {
                                              "title": str(FBUser2['first_name']) + ' '+ str(FBUser2['last_name']),
                                              "image_url": FBUser2['profile_pic'],
                                              # "subtitle": 'House : ' + str(second.house)+'\n'+'Points : '+ str(second.points)
                                              "subtitle": str(second.house)+'\n'+'Points : '+ str(second.points)
                                          },
                                          {
                                              "title": str(FBUser3['first_name']) + ' '+ str(FBUser3['last_name']),
                                              "image_url": FBUser3['profile_pic'],
                                              "subtitle":str(third.house)+'\n'+'Points : '+ str(third.points)
                                          }
                                      ]
                                  }
                              }
                          }
                      }),
                      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print r.text

def handleEveryDayPoints(db,user_id):
    user = dbAPI.user_exists(db,user_id)
    if user.house:
        house = user.house
        house_obj = House.query.filter_by(name=house).first()
        now = datetime.now()
        if user.last_day_seen:
            print 'Last Day is : '+ str(user.last_day_seen)
            if user.last_day_seen != str(now.day):
                print 'Falseeeeee'
                print ' Now is ' + str(now.day)
                user.last_day_seen = now.day
                send_message(user_id, 'You still didn\'t get your everyday 10 Points!!')
                send_message(user_id, '10 Point to ' + str(house))
                user_points = user.points
                house_points = house_obj.points
                user_points += 10
                house_points += 10
                user.points = user_points
                house_obj.points = house_points
                db.session.commit()
        else:
            user.last_day_seen = now.day
            send_message(user_id, 'You still didn\'t get your everyday 10 Points!!')
            send_message(user_id, '10 Point to ' + str(house))
            user_points = user.points
            house_points = house_obj.points
            user_points += 10
            house_points += 10
            user.points = user_points
            house_obj.points = house_points
            db.session.commit()

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

def pointsInstructions(user_id):
    points1 = {
        "title": "Answer Trivia questions correctly",
        "image_url": url_for('static', filename="assets/img/wrong4.jpg", _external=True),
    }
    points2 = {
        "title": "Share Harry Botter with a friend and get him to use it",
        "image_url": url_for('static', filename="assets/img/share.jpg", _external=True),
    }
    points3 = {
        "title": "Everyday you interact with Harry Botter you get 10 Points",
        "image_url": url_for('static', filename="assets/img/points3.jpg", _external=True),
    }
    options = [points1,points2,points3]
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=json.dumps({
                          "recipient": {"id": user_id},
                          "message": {
                              "attachment": {
                                  "type": "template",
                                  "payload": {
                                      "template_type": "generic",
                                      "elements": options
                                  }
                              }
                          }
                      }),
                      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print r.text

def getpoints(user_id):
    pointsInstructions(user_id)
    data = {
        "recipient": {"id": user_id},
        "message": {
            "text": 'Now, What do you want to do?',
            "quick_replies": [
                {
                    "content_type": "text",
                    "title": 'Trivia',
                    "payload": 'Harry_Botter_Trivia_Question'
                },
                {
                    "content_type": "text",
                    "title": 'Share',
                    "payload": 'Harry_Botter_Share'
                }
            ]
        }
    }
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": os.environ["PAGE_ACCESS_TOKEN"]},
                      data=json.dumps(data),
                      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print r.text

def GreateHallReplies(user_id):
    data = {
        "recipient": {"id": user_id},
        "message": {
            "text": 'Where do you want to go next ?',
            "quick_replies": [
                {
                    "content_type": "text",
                    "title": 'My House',
                    "payload": 'Harry_Botter_House'
                },
                {
                    "content_type": "text",
                    "title": 'My Profile',
                    "payload": 'Harry_Botter_Profile'
                },
                {
                    "content_type": "text",
                    "title": 'All Houses',
                    "payload": 'Harry_Botter_Houses'
                },
                {
                    "content_type": "text",
                    "title": 'Leaderboard',
                    "payload": 'Harry_Botter_LeaderBoard'
                },
                {
                    "content_type": "text",
                    "title": 'Trivia',
                    "payload": 'Harry_Botter_Trivia_Question'
                }
            ]
        }
    }
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": os.environ["PAGE_ACCESS_TOKEN"]},
                      data=json.dumps(data),
                      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print r.text

def handleLicense(user_id):
    obj = {
        "title":'All Content is licensed to Harry Potter Wiki under CC BY-SA 3',
        "subtitle":'No edit has been done to the original content.',
        "image_url": 'https://vignette2.wikia.nocookie.net/harrypotter/images/5/52/Harry-potter-wiki-welcome.png/revision/latest?cb=20170303211316',
        "buttons": [
            {
                "type": "web_url",
                "url": "http://harrypotter.wikia.com/wiki/Main_Page",
                "title": "Harry Potter Wiki"
            },
            {
                "type": "web_url",
                "url": "https://creativecommons.org/licenses/by-sa/3.0/legalcode",
                "title": "CC BY-SA 3"

            }
        ]
    }

    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=json.dumps({
                          "recipient": {"id": user_id},
                          "message": {
                              "attachment": {
                                  "type": "template",
                                  "payload": {
                                      "template_type": "generic",
                                      "elements": obj
                                  }
                              }
                          }
                      }),
                      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print r.text

def log(message):  # simple wrapper for logging to stdout on heroku
    # print str(message)
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)