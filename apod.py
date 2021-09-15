import obspython as obs
import urllib.request
import urllib.error
from html.parser import HTMLParser
import datetime
from random import randint
#import feedparser #THIS NEEDS TO BE INSTALLED MANUALY ASWELL AS SMGLLIB

url         = "" # Url for APOD
rssulr = "" # Url for APOD rss feed
Bsource_name = "" # Browser source
Tsource_name = "" # Text source
imagesrc = "" # Relative image source link
imagelink = "" # Actual image source link that is inserted
descriptionText = ""
refreshtime = 10

# YOINKED STRAIGHT FROM https://docs.python.org/3/library/html.parser.html
# This Parser is made to get the IMG from the HTML and put it at imagesrc
# It can also get the description text and put that at descriptionText
class MyHTMLParser(HTMLParser):
    global imagesrc
    def handle_starttag(self, tag, attrs):
        global imagesrc
        if tag == "img": # Look for image tags
            for n in attrs:
                if n[0] == "src": 
                        imagesrc = n[1]

parser = MyHTMLParser() # Create the parser

# REQUEST AND UPDATE CODE------------------------------------------------------------

def update():
    global url
    global Bsource_name
    global imagesrc
    
    # UPDATE THE IMAGE
    source = obs.obs_get_source_by_name(Bsource_name) # Call the OBS API for the source that we are gona play with
    if source is not None:
        currenturl = url
        dayoffset = (int(datetime.datetime.today().strftime("%Y%m%d")) * 975128347821798321893) % 365  # Textmash go brrrrr
        date = datetime.datetime.today() - datetime.timedelta(days = dayoffset)
        try:
            # This part will check if there was an image found (sometimes they put a video or smth) 
            # In that case, it will chose a random date between 100 days ago and 400 days ago
            # If that fails, it will just go for the next day until it can find smth good
            while imagesrc == "":
                with urllib.request.urlopen(currenturl) as response: # Make a request to the server to get the html back
                    data = response.read()
                    text = data.decode('utf-8') # Decode the HTML
                    parser.feed(text) # Parse it for text and images
                
                if imagesrc == "": 
                    date = date + datetime.timedelta(days = 1)
                    currenturl = url + "ap" + date.strftime("%y%m%d") + ".html"
                    # obs.script_log(obs.LOG_DEBUG, currenturl)
                    # obs.remove_current_callback()        
            imagelink = url + imagesrc # Make the absolute link for the image
            # Put it into the obs source
            settings = obs.obs_data_create()
            obs.obs_data_set_string(settings, "url", imagelink)
            obs.obs_source_update(source, settings)
            obs.obs_data_release(settings) # #NoMemLeaks

        except urllib.error.URLError as err:
            obs.script_log(obs.LOG_WARNING, "Error opening URL '" + url + "': " + err.reason)
            obs.remove_current_callback()

        obs.obs_source_release(source) # #NoMemLeaks

    # UPDATE THE TITLE
    #NOTDONE
    # source = obs.obs_get_source_by_name(Tsource_name) # Call the OBS API for the source that we are gona play with
    # if source is not None:
    #     try:
    #         title = ""
    #         NewsFeed = feedparser.parse("https://timesofindia.indiatimes.com/rssfeedstopstories.cms")
    #         # Put it into the obs source
    #         settings = obs.obs_data_create()
    #         obs.obs_data_set_string(settings, "text", title)
    #         obs.obs_source_update(source, settings)
    #         obs.obs_data_release(settings) # #NoMemLeaks

    #     except err:
    #         obs.script_log(obs.LOG_WARNING, "Error reading RSS feed '" + url + "': " + err.reason)
    #         obs.remove_current_callback()

    #     obs.obs_source_release(source) # #NoMemLeaks

def refresh_pressed(props, prop): # Used to make the button run and refresh the image and text
    update() 

# OBS SETTINGS STUFF------------------------------------------------------------

def script_description():
    return "Gets the APOD picutre link and sets it to a Browser Source\n\nBy twitch.tv/SuperZooper3"

def script_update(settings): # Sets the python variables to what is in OBS
    global url
    global Bsource_name
    global Tsource_name
    global refreshtime

    url         = obs.obs_data_get_string(settings, "url")
    Bsource_name = obs.obs_data_get_string(settings, "Bsource")
    Tsource_name = obs.obs_data_get_string(settings, "Tsource")
    refreshtime = obs.obs_data_get_int(settings, "refresh")

    # Lil timer to make it automaticaly refresh every 5 minutes
    obs.timer_remove(update)

    if url != "" and Bsource_name != "" and Tsource_name != "" :
        obs.timer_add(update, refreshtime * 60 * 1000)

def script_defaults(settings): # Sets the defaults for the values in the obs editor
    obs.obs_data_set_default_string(settings, "url", "https://apod.nasa.gov/apod/")
    obs.obs_data_set_default_string(settings, "rssurl", "https://apod.nasa.gov/apod.rss")

def script_properties(): # Get the property boxes so we can type them in in the scripts pannel
    props = obs.obs_properties_create()

    # Browser Source
    obs.obs_properties_add_int(props, "refresh", "Refresh Time", 10, 3600, 1)
    obs.obs_properties_add_text(props, "url", "URL", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "rssurl", "RSS URL", obs.OBS_TEXT_DEFAULT)
    p = obs.obs_properties_add_list(props, "Bsource", "Browser Source", obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
    sources = obs.obs_enum_sources()
    if sources is not None:
        for source in sources:
            source_id = obs.obs_source_get_unversioned_id(source)
            if source_id == "browser_source":
                name = obs.obs_source_get_name(source)
                obs.obs_property_list_add_string(p, name, name)

        obs.source_list_release(sources)

    # Text source
    p = obs.obs_properties_add_list(props, "Tsource", "Text Source", obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
    sources = obs.obs_enum_sources()
    if sources is not None:
        for source in sources:
            source_id = obs.obs_source_get_unversioned_id(source)
            if source_id == "text_gdiplus" or source_id == "text_ft2_source":
                name = obs.obs_source_get_name(source)
                obs.obs_property_list_add_string(p, name, name)

        obs.source_list_release(sources)

    # Button to refresh the PAGE
    obs.obs_properties_add_button(props, "button", "Refresh", refresh_pressed)
    return props
